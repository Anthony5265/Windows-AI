"""Lightweight deterministic stereo 3-D reconstruction utilities."""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import logging
import uuid
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class Reconstruction3DResult:
    result_id: str
    data: Dict[str, Any]
    confidence: float

@dataclass
class PointCloud:
    points: np.ndarray
    colors: Optional[np.ndarray] = None

@dataclass
class CameraMatrix:
    K: np.ndarray
    R: np.ndarray
    t: np.ndarray
    @property
    def projection(self) -> np.ndarray:
        return self.K @ np.hstack((self.R, self.t.reshape(3, 1)))

def _default_intrinsic(width: int = 640, height: int = 480) -> np.ndarray:
    if width <= 0 or height <= 0: raise ValueError("image dimensions must be positive")
    f = float(max(width, height))
    return np.array([[f, 0., width/2], [0., f, height/2], [0., 0., 1.]], dtype=float)

def _convolve2d(img, kernel):
    if img.ndim != 2 or kernel.ndim != 2: raise ValueError("2-D arrays required")
    ph, pw = kernel.shape[0]//2, kernel.shape[1]//2
    padded = np.pad(img, ((ph,ph),(pw,pw)), mode="reflect")
    out = np.zeros_like(img, dtype=float)
    for i in range(kernel.shape[0]):
        for j in range(kernel.shape[1]): out += kernel[i,j]*padded[i:i+img.shape[0], j:j+img.shape[1]]
    return out

def _sobel_x(img): return _convolve2d(img, np.array([[-1,0,1],[-2,0,2],[-1,0,1]], float))
def _sobel_y(img): return _convolve2d(img, np.array([[-1,-2,-1],[0,0,0],[1,2,1]], float))

def _harris_corners(gray, k=.04, threshold=.01, max_points=500):
    if max_points <= 0: raise ValueError("max_points must be positive")
    ix, iy = _sobel_x(gray), _sobel_y(gray)
    kernel = np.ones((5,5), float)/25
    ixx, iyy, ixy = (_convolve2d(v, kernel) for v in (ix*ix, iy*iy, ix*iy))
    r = ixx*iyy - ixy*ixy - k*(ixx+iyy)**2
    limit = threshold*float(r.max()) if r.size and r.max() > 0 else 0.
    coords = np.argwhere(r > limit)
    if len(coords) > max_points:
        scores = r[coords[:,0], coords[:,1]]
        coords = coords[np.argsort(scores)[-max_points:]]
    return coords

def _ncc_match(patch1, patch2):
    a, b = patch1.astype(float).ravel(), patch2.astype(float).ravel()
    a -= a.mean(); b -= b.mean(); denom = np.linalg.norm(a)*np.linalg.norm(b)
    return -1. if denom <= 1e-12 else float(np.dot(a,b)/denom)

def match_features(gray1, gray2, patch_size=11, ncc_thresh=.7, max_points=300):
    a, b = np.asarray(gray1,float), np.asarray(gray2,float)
    if a.ndim != 2 or b.ndim != 2: raise ValueError("match_features expects 2-D grayscale images")
    if patch_size < 3 or patch_size % 2 == 0: raise ValueError("patch_size must be odd and >= 3")
    if not -1 <= ncc_thresh <= 1: raise ValueError("ncc_thresh must be between -1 and 1")
    if max_points <= 0: raise ValueError("max_points must be positive")
    p1, p2 = _harris_corners(a,max_points=max_points), _harris_corners(b,max_points=max_points); h=patch_size//2
    def valid(p,s): return p[(p[:,0]>=h)&(p[:,0]<s[0]-h)&(p[:,1]>=h)&(p[:,1]<s[1]-h)]
    p1,p2=valid(p1,a.shape),valid(p2,b.shape)
    if not len(p1) or not len(p2): return np.empty((0,2),int),np.empty((0,2),int)
    out1,out2=[],[]; used=set()
    for r1,c1 in p1:
        q1=a[r1-h:r1+h+1,c1-h:c1+h+1]; best=(-1.,-1)
        for j,(r2,c2) in enumerate(p2):
            if j in used: continue
            score=_ncc_match(q1,b[r2-h:r2+h+1,c2-h:c2+h+1])
            if score>best[0]: best=(score,j)
        if best[1]>=0 and best[0]>=ncc_thresh: out1.append((r1,c1));out2.append(p2[best[1]]);used.add(best[1])
    return np.asarray(out1),np.asarray(out2)

def triangulate_points(P1,P2,pts1,pts2):
    P1,P2=np.asarray(P1,float),np.asarray(P2,float); a,b=np.asarray(pts1,float),np.asarray(pts2,float)
    if P1.shape!=(3,4) or P2.shape!=(3,4): raise ValueError("projection matrices must be (3,4)")
    if a.shape!=b.shape or a.ndim!=2 or a.shape[1]!=2: raise ValueError("point arrays must have shape (N,2)")
    out=np.full((len(a),3),np.nan)
    for i,((x1,y1),(x2,y2)) in enumerate(zip(a,b)):
        A=np.vstack((x1*P1[2]-P1[0],y1*P1[2]-P1[1],x2*P2[2]-P2[0],y2*P2[2]-P2[1]))
        _,_,vt=np.linalg.svd(A); X=vt[-1]
        if abs(X[3])>1e-12: out[i]=X[:3]/X[3]
    return out

def estimate_fundamental(pts1,pts2):
    a,b=np.asarray(pts1,float),np.asarray(pts2,float)
    if a.shape!=b.shape or a.ndim!=2 or a.shape[1]!=2: raise ValueError("point arrays must have shape (N,2)")
    if len(a)<8: raise ValueError("at least 8 point correspondences are required")
    A=np.array([[x2*x1,x2*y1,x2,y2*x1,y2*y1,y2,x1,y1,1] for (x1,y1),(x2,y2) in zip(a,b)],float)
    _,_,vt=np.linalg.svd(A); F=vt[-1].reshape(3,3); U,S,Vt=np.linalg.svd(F); S[-1]=0; F=U@np.diag(S)@Vt
    n=np.linalg.norm(F); return F/n if n>1e-12 else F

def essential_from_fundamental(F,K):
    F,K=np.asarray(F,float),np.asarray(K,float)
    if F.shape!=(3,3) or K.shape!=(3,3): raise ValueError("F and K must be (3,3)")
    return K.T@F@K

def decompose_essential(E):
    E=np.asarray(E,float)
    if E.shape!=(3,3): raise ValueError("E must be (3,3)")
    U,_,Vt=np.linalg.svd(E)
    if np.linalg.det(U)<0: U[:,-1]*=-1
    if np.linalg.det(Vt)<0: Vt[-1]*=-1
    W=np.array([[0,-1,0],[1,0,0],[0,0,1]],float); t=U[:,2]
    return [(U@W@Vt,t),(U@W@Vt,-t),(U@W.T@Vt,t),(U@W.T@Vt,-t)]

def reconstruct_stereo(gray1,gray2,K=None):
    a,b=np.asarray(gray1,float),np.asarray(gray2,float)
    if a.ndim!=2 or b.ndim!=2 or a.shape!=b.shape: raise ValueError("stereo images must be matching 2-D arrays")
    K=_default_intrinsic(a.shape[1],a.shape[0]) if K is None else np.asarray(K,float)
    if K.shape!=(3,3) or not np.all(np.isfinite(K)): raise ValueError("K must be finite and shape (3,3)")
    p1,p2=match_features(a,b,max_points=200)
    if len(p1)<8: return PointCloud(np.empty((0,3)))
    p1,p2=p1[:,::-1].astype(float),p2[:,::-1].astype(float); F=estimate_fundamental(p1,p2); E=essential_from_fundamental(F,K)
    P1=K@np.hstack((np.eye(3),np.zeros((3,1)))); best=None; best_count=-1
    for R,t in decompose_essential(E):
        P2=K@np.hstack((R,t[:,None])); cloud=triangulate_points(P1,P2,p1,p2); finite=np.all(np.isfinite(cloud),1); z2=(R@cloud.T+t[:,None])[2]; valid=finite&(cloud[:,2]>0)&(z2>0); count=int(valid.sum())
        if count>best_count: best_count=count;best=cloud[valid]
    return PointCloud(best if best is not None else np.empty((0,3)))

def approximate_mesh(cloud,grid_res=32):
    if grid_res<2: raise ValueError("grid_res must be at least 2")
    pts=np.asarray(cloud.points,float)
    if pts.ndim!=2 or pts.shape[1]!=3: raise ValueError("cloud.points must be (N,3)")
    pts=pts[np.all(np.isfinite(pts),1)]
    if not len(pts): return {"vertices":np.empty((0,3)),"triangles":np.empty((0,3),int)}
    mn,mx=pts.min(0),pts.max(0); span=np.maximum(mx-mn,1e-12); idx=np.clip(((pts-mn)/span*(grid_res-1)).astype(int),0,grid_res-1); occ=np.zeros((grid_res,grid_res,grid_res),bool);occ[tuple(idx.T)]=True
    verts=[];tris=[];step=span/grid_res
    for x,y,z in zip(*np.where(occ)):
        vi=len(verts); base=mn+np.array([x,y,z])*step; verts += [base,base+step*[1,0,0],base+step*[1,1,0],base+step*[0,1,0]];tris += [[vi,vi+1,vi+2],[vi,vi+2,vi+3]]
    return {"vertices":np.asarray(verts),"triangles":np.asarray(tris,int)}

class Reconstruction3DSystem:
    def __init__(self,data_dir): self.data_dir=Path(data_dir);self.data_dir.mkdir(parents=True,exist_ok=True);self.results=[];self.K=None
    def set_intrinsic(self,K):
        K=np.asarray(K,float)
        if K.shape!=(3,3) or not np.all(np.isfinite(K)): raise ValueError("K must be finite and shape (3,3)")
        if K[0,0]<=0 or K[1,1]<=0 or abs(K[2,2])<1e-12: raise ValueError("invalid intrinsic matrix")
        self.K=K.copy()
    def process(self,input_data):
        if not isinstance(input_data,dict) or "left" not in input_data or "right" not in input_data: raise ValueError("input_data must contain left and right images")
        cloud=reconstruct_stereo(input_data["left"],input_data["right"],self.K);mesh=approximate_mesh(cloud);n=len(cloud.points)
        result=Reconstruction3DResult(str(uuid.uuid4()),{"num_points":n,"num_vertices":len(mesh["vertices"]),"num_triangles":len(mesh["triangles"]),"bounds_min":cloud.points.min(0).tolist() if n else [],"bounds_max":cloud.points.max(0).tolist() if n else []},min(1.,n/100.))
        self.results.append(result);return result
    def reconstruct(self,gray1,gray2): return reconstruct_stereo(gray1,gray2,self.K)
    def build_mesh(self,cloud,grid_res=32): return approximate_mesh(cloud,grid_res)

_3d_reconstruction=None
def get_3d_reconstruction(): return _3d_reconstruction
def initialize_3d_reconstruction(data_dir):
    global _3d_reconstruction
    _3d_reconstruction=Reconstruction3DSystem(data_dir);return _3d_reconstruction
