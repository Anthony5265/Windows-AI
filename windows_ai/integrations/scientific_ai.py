"""
Scientific Research AI Manager - 20+ Services
Research assistance, data analysis, simulation, literature review
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)

class ScientificAIManager:
    """Unified scientific AI across 20+ services"""

    def __init__(self):
        self._initialized = False

    async def initialize(self, config: Optional[Dict] = None):
        if self._initialized:
            return
        self._initialized = True

    # ==================== LITERATURE SEARCH ====================

    async def search_papers(self, query: str, source: str = "semantic_scholar", limit: int = 20) -> List[Dict]:
        """Search academic papers"""
        import aiohttp

        if source == "semantic_scholar":
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit={limit}&fields=title,authors,year,abstract,citationCount,url"
                ) as response:
                    data = await response.json()
                    return [{
                        "title": p.get("title"),
                        "authors": [a.get("name") for a in p.get("authors", [])],
                        "year": p.get("year"),
                        "abstract": p.get("abstract"),
                        "citations": p.get("citationCount"),
                        "url": p.get("url")
                    } for p in data.get("data", [])]

        elif source == "arxiv":
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://export.arxiv.org/api/query?search_query=all:{query}&max_results={limit}"
                ) as response:
                    import xml.etree.ElementTree as ET
                    text = await response.text()
                    root = ET.fromstring(text)
                    ns = {"atom": "http://www.w3.org/2005/Atom"}
                    return [{
                        "title": entry.find("atom:title", ns).text.strip(),
                        "authors": [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)],
                        "summary": entry.find("atom:summary", ns).text.strip(),
                        "link": entry.find("atom:id", ns).text
                    } for entry in root.findall("atom:entry", ns)]

        elif source == "pubmed":
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={query}&retmax={limit}&retmode=json"
                ) as response:
                    data = await response.json()
                    ids = data.get("esearchresult", {}).get("idlist", [])
                    return [{"pubmed_id": id} for id in ids]

        return []

    async def get_paper_details(self, paper_id: str, source: str = "semantic_scholar") -> Dict:
        """Get detailed paper information"""
        import aiohttp

        if source == "semantic_scholar":
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}?fields=title,abstract,authors,year,citationCount,references,citations"
                ) as response:
                    return await response.json()

        return {}

    # ==================== DATA ANALYSIS ====================

    async def statistical_analysis(self, data: List[float]) -> Dict:
        """Perform statistical analysis"""
        from scipy import stats

        arr = np.array(data)

        return {
            "count": len(arr),
            "mean": float(np.mean(arr)),
            "median": float(np.median(arr)),
            "std": float(np.std(arr)),
            "variance": float(np.var(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "quartiles": {
                "q1": float(np.percentile(arr, 25)),
                "q2": float(np.percentile(arr, 50)),
                "q3": float(np.percentile(arr, 75))
            },
            "skewness": float(stats.skew(arr)),
            "kurtosis": float(stats.kurtosis(arr)),
            "normality_test": {
                "statistic": float(stats.normaltest(arr).statistic) if len(arr) >= 8 else None,
                "p_value": float(stats.normaltest(arr).pvalue) if len(arr) >= 8 else None
            }
        }

    async def hypothesis_test(self, sample1: List[float], sample2: List[float] = None, test_type: str = "ttest") -> Dict:
        """Perform hypothesis testing"""
        from scipy import stats

        arr1 = np.array(sample1)

        if test_type == "ttest" and sample2:
            arr2 = np.array(sample2)
            stat, pvalue = stats.ttest_ind(arr1, arr2)
            return {"test": "independent_t_test", "statistic": float(stat), "p_value": float(pvalue),
                    "significant": pvalue < 0.05}

        elif test_type == "ttest_1samp":
            stat, pvalue = stats.ttest_1samp(arr1, 0)
            return {"test": "one_sample_t_test", "statistic": float(stat), "p_value": float(pvalue),
                    "significant": pvalue < 0.05}

        elif test_type == "anova" and sample2:
            arr2 = np.array(sample2)
            stat, pvalue = stats.f_oneway(arr1, arr2)
            return {"test": "anova", "statistic": float(stat), "p_value": float(pvalue),
                    "significant": pvalue < 0.05}

        elif test_type == "chi2" and sample2:
            arr2 = np.array(sample2)
            stat, pvalue = stats.chisquare(arr1, arr2)
            return {"test": "chi_square", "statistic": float(stat), "p_value": float(pvalue),
                    "significant": pvalue < 0.05}

        return {"error": "Invalid test configuration"}

    async def correlation_analysis(self, data: Dict[str, List[float]]) -> Dict:
        """Analyze correlations between variables"""
        from scipy import stats
        import pandas as pd

        df = pd.DataFrame(data)
        correlation_matrix = df.corr().to_dict()

        # Calculate p-values
        p_values = {}
        columns = df.columns.tolist()
        for i, col1 in enumerate(columns):
            p_values[col1] = {}
            for col2 in columns:
                if col1 != col2:
                    _, p = stats.pearsonr(df[col1], df[col2])
                    p_values[col1][col2] = float(p)
                else:
                    p_values[col1][col2] = 0.0

        return {"correlations": correlation_matrix, "p_values": p_values}

    async def regression_analysis(self, x: List[float], y: List[float], regression_type: str = "linear") -> Dict:
        """Perform regression analysis"""
        from scipy import stats
        from sklearn.linear_model import LinearRegression, Ridge, Lasso
        from sklearn.preprocessing import PolynomialFeatures
        from sklearn.metrics import r2_score, mean_squared_error

        X = np.array(x).reshape(-1, 1)
        Y = np.array(y)

        if regression_type == "linear":
            model = LinearRegression()
            model.fit(X, Y)
            predictions = model.predict(X)

            return {
                "type": "linear",
                "coefficient": float(model.coef_[0]),
                "intercept": float(model.intercept_),
                "r_squared": float(r2_score(Y, predictions)),
                "rmse": float(np.sqrt(mean_squared_error(Y, predictions)))
            }

        elif regression_type == "polynomial":
            poly = PolynomialFeatures(degree=2)
            X_poly = poly.fit_transform(X)
            model = LinearRegression()
            model.fit(X_poly, Y)
            predictions = model.predict(X_poly)

            return {
                "type": "polynomial",
                "coefficients": model.coef_.tolist(),
                "intercept": float(model.intercept_),
                "r_squared": float(r2_score(Y, predictions))
            }

        return {}

    # ==================== MOLECULAR ANALYSIS ====================

    async def analyze_molecule(self, smiles: str) -> Dict:
        """Analyze molecular structure"""
        from rdkit import Chem
        from rdkit.Chem import Descriptors, AllChem

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return {"error": "Invalid SMILES"}

        return {
            "smiles": smiles,
            "molecular_weight": Descriptors.MolWt(mol),
            "logp": Descriptors.MolLogP(mol),
            "num_atoms": mol.GetNumAtoms(),
            "num_bonds": mol.GetNumBonds(),
            "num_rings": Descriptors.RingCount(mol),
            "hbd": Descriptors.NumHDonors(mol),
            "hba": Descriptors.NumHAcceptors(mol),
            "tpsa": Descriptors.TPSA(mol),
            "rotatable_bonds": Descriptors.NumRotatableBonds(mol)
        }

    async def predict_protein_structure(self, sequence: str) -> Dict:
        """Predict protein structure (using ESMFold API)"""
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.esmatlas.com/foldSequence/v1/pdb/",
                data=sequence,
                headers={"Content-Type": "text/plain"}
            ) as response:
                if response.status == 200:
                    pdb = await response.text()
                    return {"sequence": sequence, "pdb": pdb, "length": len(sequence)}

        return {"error": "Prediction failed"}

    # ==================== RESEARCH ASSISTANT ====================

    async def research_assistant(self, question: str, context: str = None) -> Dict:
        """AI research assistant"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": """You are a scientific research assistant.
Provide accurate, well-reasoned answers with citations when possible.
Explain complex concepts clearly.
Acknowledge uncertainty and limitations."""},
            {"role": "user", "content": f"Question: {question}\n\nContext: {context or 'General scientific inquiry'}"}
        ]

        response = await ai.chat(Provider.OPENAI, messages, model="gpt-4o")
        return {"answer": response["content"]}

    async def generate_hypothesis(self, observations: List[str], field: str) -> Dict:
        """Generate scientific hypotheses"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": f"""Generate scientific hypotheses based on observations in {field}.
For each hypothesis provide:
1. Statement
2. Rationale
3. Testable predictions
4. Suggested experiments
Return JSON array of hypotheses."""},
            {"role": "user", "content": f"Observations:\n" + "\n".join(observations)}
        ]

        response = await ai.chat(Provider.OPENAI, messages, model="gpt-4o")
        import json
        try:
            return {"hypotheses": json.loads(response["content"])}
        except:
            return {"hypotheses": response["content"]}

    async def design_experiment(self, hypothesis: str, constraints: Dict = None) -> Dict:
        """Design experiment to test hypothesis"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": """Design a rigorous experiment including:
1. Experimental design (RCT, factorial, etc.)
2. Variables (independent, dependent, controlled)
3. Sample size and power analysis
4. Methods and materials
5. Data collection procedures
6. Statistical analysis plan
7. Potential confounds and controls
Return detailed JSON."""},
            {"role": "user", "content": f"Hypothesis: {hypothesis}\nConstraints: {constraints or 'None'}"}
        ]

        response = await ai.chat(Provider.OPENAI, messages, model="gpt-4o")
        import json
        try:
            return json.loads(response["content"])
        except:
            return {"design": response["content"]}

    def list_capabilities(self) -> Dict[str, List[str]]:
        return {
            "literature": ["semantic_scholar", "arxiv", "pubmed", "google_scholar"],
            "statistics": ["descriptive", "hypothesis_testing", "correlation", "regression"],
            "molecular": ["structure_analysis", "protein_prediction", "drug_design"],
            "research": ["hypothesis_generation", "experiment_design", "data_interpretation"]
        }
