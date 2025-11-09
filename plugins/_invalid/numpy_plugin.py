"""
NumPy plugin for Windows AI - provides numerical computing capabilities
"""

import numpy as np
from typing import Any, Dict, List, Optional, Union
import json
import logging

logger = logging.getLogger(__name__)

class NumpyPlugin:
    """NumPy integration plugin for numerical operations"""
    
    def __init__(self):
        self.name = "numpy"
        self.version = "1.0.0"
        self.description = "NumPy numerical computing plugin"
        self.author = "Windows AI"
        
    def get_info(self) -> Dict[str, Any]:
        """Return plugin information"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "capabilities": [
                "array_creation",
                "array_manipulation",
                "mathematical_operations",
                "linear_algebra",
                "statistics",
                "random_sampling"
            ]
        }
    
    def create_array(self, data: Union[List, tuple], dtype: Optional[str] = None) -> Dict[str, Any]:
        """Create a NumPy array from data"""
        try:
            if dtype:
                arr = np.array(data, dtype=dtype)
            else:
                arr = np.array(data)
            
            return {
                "success": True,
                "array": arr.tolist(),
                "shape": arr.shape,
                "dtype": str(arr.dtype),
                "size": arr.size
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_zeros(self, shape: tuple, dtype: Optional[str] = None) -> Dict[str, Any]:
        """Create array filled with zeros"""
        try:
            if dtype:
                arr = np.zeros(shape, dtype=dtype)
            else:
                arr = np.zeros(shape)
            
            return {
                "success": True,
                "array": arr.tolist(),
                "shape": arr.shape,
                "dtype": str(arr.dtype)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_ones(self, shape: tuple, dtype: Optional[str] = None) -> Dict[str, Any]:
        """Create array filled with ones"""
        try:
            if dtype:
                arr = np.ones(shape, dtype=dtype)
            else:
                arr = np.ones(shape)
            
            return {
                "success": True,
                "array": arr.tolist(),
                "shape": arr.shape,
                "dtype": str(arr.dtype)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_arange(self, start: int, stop: Optional[int] = None, step: int = 1) -> Dict[str, Any]:
        """Create array with evenly spaced values"""
        try:
            if stop is None:
                arr = np.arange(start)
            else:
                arr = np.arange(start, stop, step)
            
            return {
                "success": True,
                "array": arr.tolist(),
                "shape": arr.shape,
                "dtype": str(arr.dtype)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_linspace(self, start: float, stop: float, num: int = 50) -> Dict[str, Any]:
        """Create array with evenly spaced numbers over interval"""
        try:
            arr = np.linspace(start, stop, num)
            
            return {
                "success": True,
                "array": arr.tolist(),
                "shape": arr.shape,
                "dtype": str(arr.dtype)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def array_info(self, data: List) -> Dict[str, Any]:
        """Get information about an array"""
        try:
            arr = np.array(data)
            
            return {
                "success": True,
                "shape": arr.shape,
                "dtype": str(arr.dtype),
                "size": arr.size,
                "ndim": arr.ndim,
                "min": float(arr.min()) if arr.size > 0 else None,
                "max": float(arr.max()) if arr.size > 0 else None,
                "mean": float(arr.mean()) if arr.size > 0 else None,
                "std": float(arr.std()) if arr.size > 0 else None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def reshape_array(self, data: List, new_shape: tuple) -> Dict[str, Any]:
        """Reshape an array"""
        try:
            arr = np.array(data)
            reshaped = arr.reshape(new_shape)
            
            return {
                "success": True,
                "original_shape": arr.shape,
                "new_shape": reshaped.shape,
                "array": reshaped.tolist()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def transpose_array(self, data: List) -> Dict[str, Any]:
        """Transpose an array"""
        try:
            arr = np.array(data)
            transposed = arr.T
            
            return {
                "success": True,
                "original_shape": arr.shape,
                "transposed_shape": transposed.shape,
                "array": transposed.tolist()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def mathematical_operations(self, data: List, operation: str, other: Optional[Union[List, float, int]] = None) -> Dict[str, Any]:
        """Perform mathematical operations on arrays"""
        try:
            arr = np.array(data)
            
            if operation == "add":
                if other is not None:
                    if isinstance(other, (list, tuple)):
                        result = arr + np.array(other)
                    else:
                        result = arr + other
                else:
                    return {"success": False, "error": "Add operation requires second operand"}
            elif operation == "subtract":
                if other is not None:
                    if isinstance(other, (list, tuple)):
                        result = arr - np.array(other)
                    else:
                        result = arr - other
                else:
                    return {"success": False, "error": "Subtract operation requires second operand"}
            elif operation == "multiply":
                if other is not None:
                    if isinstance(other, (list, tuple)):
                        result = arr * np.array(other)
                    else:
                        result = arr * other
                else:
                    return {"success": False, "error": "Multiply operation requires second operand"}
            elif operation == "divide":
                if other is not None:
                    if isinstance(other, (list, tuple)):
                        result = arr / np.array(other)
                    else:
                        result = arr / other
                else:
                    return {"success": False, "error": "Divide operation requires second operand"}
            elif operation == "power":
                if other is not None:
                    result = np.power(arr, other)
                else:
                    return {"success": False, "error": "Power operation requires exponent"}
            elif operation == "sqrt":
                result = np.sqrt(arr)
            elif operation == "abs":
                result = np.abs(arr)
            elif operation == "exp":
                result = np.exp(arr)
            elif operation == "log":
                result = np.log(arr)
            elif operation == "sin":
                result = np.sin(arr)
            elif operation == "cos":
                result = np.cos(arr)
            elif operation == "tan":
                result = np.tan(arr)
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
            
            return {
                "success": True,
                "operation": operation,
                "result": result.tolist(),
                "shape": result.shape
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def statistical_operations(self, data: List, operation: str, axis: Optional[int] = None) -> Dict[str, Any]:
        """Perform statistical operations on arrays"""
        try:
            arr = np.array(data)
            
            if operation == "mean":
                result = arr.mean(axis=axis)
            elif operation == "median":
                result = np.median(arr, axis=axis)
            elif operation == "std":
                result = arr.std(axis=axis)
            elif operation == "var":
                result = arr.var(axis=axis)
            elif operation == "min":
                result = arr.min(axis=axis)
            elif operation == "max":
                result = arr.max(axis=axis)
            elif operation == "sum":
                result = arr.sum(axis=axis)
            elif operation == "prod":
                result = arr.prod(axis=axis)
            elif operation == "argmin":
                result = arr.argmin(axis=axis)
            elif operation == "argmax":
                result = arr.argmax(axis=axis)
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
            
            # Convert numpy scalar to Python scalar if needed
            if np.isscalar(result):
                result = result.item()
            elif isinstance(result, np.ndarray):
                result = result.tolist()
            
            return {
                "success": True,
                "operation": operation,
                "axis": axis,
                "result": result
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def linear_algebra_operations(self, data1: List, operation: str, data2: Optional[List] = None) -> Dict[str, Any]:
        """Perform linear algebra operations"""
        try:
            arr1 = np.array(data1)
            
            if operation == "dot":
                if data2 is None:
                    return {"success": False, "error": "Dot product requires second array"}
                arr2 = np.array(data2)
                result = np.dot(arr1, arr2)
            elif operation == "matmul":
                if data2 is None:
                    return {"success": False, "error": "Matrix multiplication requires second array"}
                arr2 = np.array(data2)
                result = np.matmul(arr1, arr2)
            elif operation == "determinant":
                if arr1.ndim != 2 or arr1.shape[0] != arr1.shape[1]:
                    return {"success": False, "error": "Determinant requires square matrix"}
                result = np.linalg.det(arr1)
            elif operation == "inverse":
                if arr1.ndim != 2 or arr1.shape[0] != arr1.shape[1]:
                    return {"success": False, "error": "Inverse requires square matrix"}
                result = np.linalg.inv(arr1)
            elif operation == "eigenvectors":
                if arr1.ndim != 2 or arr1.shape[0] != arr1.shape[1]:
                    return {"success": False, "error": "Eigen decomposition requires square matrix"}
                eigenvalues, eigenvectors = np.linalg.eig(arr1)
                result = {
                    "eigenvalues": eigenvalues.tolist(),
                    "eigenvectors": eigenvectors.tolist()
                }
            elif operation == "svd":
                if arr1.ndim != 2:
                    return {"success": False, "error": "SVD requires 2D matrix"}
                u, s, vh = np.linalg.svd(arr1)
                result = {
                    "u": u.tolist(),
                    "s": s.tolist(),
                    "vh": vh.tolist()
                }
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
            
            # Convert result to list if it's a numpy array
            if isinstance(result, np.ndarray):
                result = result.tolist()
            elif np.isscalar(result):
                result = result.item()
            
            return {
                "success": True,
                "operation": operation,
                "result": result
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def random_operations(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Perform random number generation operations"""
        try:
            if operation == "random":
                size = kwargs.get("size", None)
                result = np.random.random(size)
            elif operation == "randint":
                low = kwargs.get("low", 0)
                high = kwargs.get("high", None)
                size = kwargs.get("size", None)
                result = np.random.randint(low, high, size)
            elif operation == "normal":
                loc = kwargs.get("loc", 0.0)
                scale = kwargs.get("scale", 1.0)
                size = kwargs.get("size", None)
                result = np.random.normal(loc, scale, size)
            elif operation == "uniform":
                low = kwargs.get("low", 0.0)
                high = kwargs.get("high", 1.0)
                size = kwargs.get("size", None)
                result = np.random.uniform(low, high, size)
            elif operation == "choice":
                a = kwargs.get("a", None)
                size = kwargs.get("size", None)
                replace = kwargs.get("replace", True)
                p = kwargs.get("p", None)
                result = np.random.choice(a, size, replace, p)
            elif operation == "shuffle":
                arr = np.array(kwargs.get("array", []))
                np.random.shuffle(arr)
                result = arr
            elif operation == "seed":
                seed = kwargs.get("seed", None)
                np.random.seed(seed)
                result = f"Random seed set to {seed}"
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
            
            # Convert result to list if it's a numpy array
            if isinstance(result, np.ndarray):
                result = result.tolist()
            
            return {
                "success": True,
                "operation": operation,
                "result": result
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def array_indexing(self, data: List, indices: Any) -> Dict[str, Any]:
        """Perform array indexing operations"""
        try:
            arr = np.array(data)
            
            # Handle different types of indexing
            if isinstance(indices, dict):
                if "slice" in indices:
                    slice_obj = slice(*indices["slice"])
                    result = arr[slice_obj]
                elif "boolean" in indices:
                    bool_mask = np.array(indices["boolean"])
                    result = arr[bool_mask]
                elif "fancy" in indices:
                    fancy_indices = indices["fancy"]
                    result = arr[fancy_indices]
                else:
                    return {"success": False, "error": "Unknown indexing type"}
            else:
                result = arr[indices]
            
            return {
                "success": True,
                "result": result.tolist() if isinstance(result, np.ndarray) else result,
                "shape": result.shape if isinstance(result, np.ndarray) else None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def array_concatenation(self, arrays: List[List], axis: int = 0) -> Dict[str, Any]:
        """Concatenate arrays"""
        try:
            np_arrays = [np.array(arr) for arr in arrays]
            result = np.concatenate(np_arrays, axis=axis)
            
            return {
                "success": True,
                "result": result.tolist(),
                "shape": result.shape,
                "axis": axis
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def array_splitting(self, data: List, sections: int, axis: int = 0) -> Dict[str, Any]:
        """Split array into sub-arrays"""
        try:
            arr = np.array(data)
            result = np.split(arr, sections, axis=axis)
            
            return {
                "success": True,
                "result": [sub_arr.tolist() for sub_arr in result],
                "sections": sections,
                "axis": axis
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

# Plugin instance
plugin = NumpyPlugin()

def get_plugin():
    """Return the plugin instance"""
    return plugin

def get_plugin_info():
    """Return plugin information"""
    return plugin.get_info()