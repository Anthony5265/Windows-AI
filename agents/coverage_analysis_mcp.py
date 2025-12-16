"""
Coverage Analysis MCP Server
Analyzes coverage reports, prioritizes modules, generates action plans
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Tuple
import logging
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)


@dataclass
class CoverageInfo:
    """Coverage information for a module"""
    file: str
    statements: int
    missing: int
    covered: int
    percent: float
    branches_total: int = 0
    branches_covered: int = 0
    branch_percent: float = 0.0
    
    @property
    def priority_score(self) -> float:
        """Calculate priority score (higher = more important)"""
        # Factors: coverage gap, file size, criticality
        gap = self.missing
        size_factor = min(self.statements / 100, 5.0)  # Cap at 5x
        criticality = self._get_criticality()
        
        return gap * size_factor * criticality
    
    def _get_criticality(self) -> float:
        """Determine how critical this module is"""
        critical_patterns = [
            (r"core/orchestrator", 5.0),
            (r"core/", 4.0),
            (r"security/", 4.5),
            (r"agents/", 4.0),
            (r"api/", 3.5),
            (r"plugins/base", 3.5),
            (r"managers/", 2.5),
            (r"integrations/", 2.0),
            (r"__init__", 1.0),
        ]
        
        for pattern, score in critical_patterns:
            if re.search(pattern, self.file):
                return score
        
        return 1.5  # Default


class CoverageAnalysisMCP:
    """
    MCP Server for analyzing coverage reports
    
    Capabilities:
    - Parse coverage.xml and htmlcov/ reports
    - Identify coverage gaps and prioritize fixes
    - Generate actionable task lists
    - Track coverage progress over time
    - Recommend test strategies
    """
    
    def __init__(self):
        self.coverage_data: Dict[str, CoverageInfo] = {}
        self.total_statements = 0
        self.total_covered = 0
        self.total_missing = 0
    
    def parse_coverage_xml(self, xml_file: str) -> Dict[str, Any]:
        """
        Parse coverage.xml file
        
        Args:
            xml_file: Path to coverage.xml
        
        Returns:
            Parsed coverage data with statistics
        """
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            self.coverage_data.clear()
            self.total_statements = 0
            self.total_covered = 0
            self.total_missing = 0
            
            for package in root.findall('.//package'):
                for cls in package.findall('classes/class'):
                    filename = cls.get('filename', '')
                    
                    # Get statement coverage
                    lines = cls.findall('lines/line')
                    total_lines = len(lines)
                    covered_lines = sum(1 for line in lines if line.get('hits', '0') != '0')
                    missing_lines = total_lines - covered_lines
                    
                    # Get branch coverage if available
                    branches_total = 0
                    branches_covered = 0
                    for line in lines:
                        branch = line.get('branch')
                        if branch == 'true':
                            branches_total += 1
                            if line.get('hits', '0') != '0':
                                branches_covered += 1
                    
                    # Calculate percentages
                    stmt_percent = (covered_lines / total_lines * 100) if total_lines > 0 else 0.0
                    branch_percent = (branches_covered / branches_total * 100) if branches_total > 0 else 0.0
                    
                    self.coverage_data[filename] = CoverageInfo(
                        file=filename,
                        statements=total_lines,
                        missing=missing_lines,
                        covered=covered_lines,
                        percent=stmt_percent,
                        branches_total=branches_total,
                        branches_covered=branches_covered,
                        branch_percent=branch_percent
                    )
                    
                    self.total_statements += total_lines
                    self.total_covered += covered_lines
                    self.total_missing += missing_lines
            
            overall_percent = (self.total_covered / self.total_statements * 100) if self.total_statements > 0 else 0.0
            
            return {
                "total_files": len(self.coverage_data),
                "total_statements": self.total_statements,
                "covered": self.total_covered,
                "missing": self.total_missing,
                "percent": overall_percent
            }
        
        except Exception as e:
            logger.error(f"Failed to parse coverage XML: {e}")
            return {"error": str(e)}
    
    def get_prioritized_modules(self, min_missing: int = 10) -> List[CoverageInfo]:
        """
        Get modules prioritized by importance and coverage gap
        
        Args:
            min_missing: Minimum missing statements to include
        
        Returns:
            List of modules ordered by priority (highest first)
        """
        modules = [
            info for info in self.coverage_data.values()
            if info.missing >= min_missing
        ]
        
        # Sort by priority score (highest first)
        modules.sort(key=lambda x: x.priority_score, reverse=True)
        
        return modules
    
    def generate_action_plan(self, target_coverage: float = 100.0) -> Dict[str, Any]:
        """
        Generate action plan to reach target coverage
        
        Args:
            target_coverage: Target coverage percentage
        
        Returns:
            Structured action plan with tasks
        """
        current_percent = (self.total_covered / self.total_statements * 100) if self.total_statements > 0 else 0.0
        gap = target_coverage - current_percent
        
        if gap <= 0:
            return {
                "status": "complete",
                "current": current_percent,
                "target": target_coverage,
                "message": "Target coverage already achieved!"
            }
        
        # Calculate statements needed
        statements_needed = int((gap / 100) * self.total_statements)
        
        # Prioritize modules
        prioritized = self.get_prioritized_modules()
        
        # Create phases
        phases = []
        covered_so_far = 0
        
        # Phase 1: Critical modules (core, security, agents)
        phase1_modules = [m for m in prioritized if m._get_criticality() >= 4.0]
        if phase1_modules:
            phases.append({
                "name": "Phase 1: Critical Infrastructure",
                "modules": [
                    {
                        "file": m.file,
                        "missing": m.missing,
                        "percent": m.percent,
                        "priority": m.priority_score
                    }
                    for m in phase1_modules[:10]  # Top 10
                ],
                "estimated_statements": sum(m.missing for m in phase1_modules[:10])
            })
            covered_so_far += sum(m.missing for m in phase1_modules[:10])
        
        # Phase 2: High-value modules
        phase2_modules = [m for m in prioritized if 3.0 <= m._get_criticality() < 4.0]
        if phase2_modules:
            phases.append({
                "name": "Phase 2: Core Functionality",
                "modules": [
                    {
                        "file": m.file,
                        "missing": m.missing,
                        "percent": m.percent,
                        "priority": m.priority_score
                    }
                    for m in phase2_modules[:20]  # Top 20
                ],
                "estimated_statements": sum(m.missing for m in phase2_modules[:20])
            })
            covered_so_far += sum(m.missing for m in phase2_modules[:20])
        
        # Phase 3: Remaining modules
        phase3_modules = [m for m in prioritized if m._get_criticality() < 3.0]
        if phase3_modules:
            phases.append({
                "name": "Phase 3: Comprehensive Coverage",
                "modules": [
                    {
                        "file": m.file,
                        "missing": m.missing,
                        "percent": m.percent,
                        "priority": m.priority_score
                    }
                    for m in phase3_modules
                ],
                "estimated_statements": sum(m.missing for m in phase3_modules)
            })
        
        return {
            "status": "in_progress",
            "current_coverage": current_percent,
            "target_coverage": target_coverage,
            "coverage_gap": gap,
            "statements_needed": statements_needed,
            "total_files_needing_tests": len(prioritized),
            "phases": phases,
            "recommendations": self._get_recommendations(prioritized)
        }
    
    def _get_recommendations(self, modules: List[CoverageInfo]) -> List[str]:
        """Generate test strategy recommendations"""
        recommendations = []
        
        # Check for low-hanging fruit
        easy_wins = [m for m in modules if m.missing < 50 and m.percent > 50]
        if easy_wins:
            recommendations.append(f"Quick wins available: {len(easy_wins)} modules need <50 statements for 100% coverage")
        
        # Check for large gaps
        big_gaps = [m for m in modules if m.missing > 200]
        if big_gaps:
            recommendations.append(f"Large gaps: {len(big_gaps)} modules need 200+ statements. Use Test Generation Agent for efficiency")
        
        # Check branch coverage
        low_branch = [m for m in modules if m.branches_total > 0 and m.branch_percent < 70]
        if low_branch:
            recommendations.append(f"Branch coverage low: {len(low_branch)} modules need branch testing focus")
        
        # Strategy recommendations
        recommendations.append("Use Test Generation Agent for batch test creation")
        recommendations.append("Prioritize critical modules first (core, security, agents)")
        recommendations.append("Run tests frequently to track progress")
        
        return recommendations
    
    def get_module_details(self, file_path: str) -> Dict[str, Any]:
        """
        Get detailed coverage info for a specific module
        
        Args:
            file_path: Path to module
        
        Returns:
            Detailed coverage information
        """
        if file_path not in self.coverage_data:
            return {"error": "Module not found in coverage data"}
        
        info = self.coverage_data[file_path]
        
        return {
            "file": info.file,
            "statements": {
                "total": info.statements,
                "covered": info.covered,
                "missing": info.missing,
                "percent": info.percent
            },
            "branches": {
                "total": info.branches_total,
                "covered": info.branches_covered,
                "percent": info.branch_percent
            },
            "priority": {
                "score": info.priority_score,
                "criticality": info._get_criticality()
            },
            "recommendations": self._get_module_recommendations(info)
        }
    
    def _get_module_recommendations(self, info: CoverageInfo) -> List[str]:
        """Get recommendations for a specific module"""
        recs = []
        
        if info.missing < 20:
            recs.append("Small gap - can complete manually")
        elif info.missing < 100:
            recs.append("Medium gap - use Test Generator for efficiency")
        else:
            recs.append("Large gap - definitely use Test Generation Agent")
        
        if info.branches_total > 0 and info.branch_percent < 80:
            recs.append("Focus on branch coverage - test all code paths")
        
        if info._get_criticality() >= 4.0:
            recs.append("CRITICAL MODULE - prioritize 100% coverage")
        
        return recs
    
    def compare_coverage_reports(self, old_xml: str, new_xml: str) -> Dict[str, Any]:
        """
        Compare two coverage reports to track progress
        
        Args:
            old_xml: Path to old coverage.xml
            new_xml: Path to new coverage.xml
        
        Returns:
            Comparison showing improvements/regressions
        """
        # Parse old coverage
        old_data = CoverageAnalysisMCP()
        old_summary = old_data.parse_coverage_xml(old_xml)
        
        # Parse new coverage
        new_data = CoverageAnalysisMCP()
        new_summary = new_data.parse_coverage_xml(new_xml)
        
        # Calculate changes
        coverage_change = new_summary["percent"] - old_summary["percent"]
        statements_change = new_summary["covered"] - old_summary["covered"]
        
        # Find improved/regressed modules
        improved = []
        regressed = []
        
        for file, old_info in old_data.coverage_data.items():
            if file in new_data.coverage_data:
                new_info = new_data.coverage_data[file]
                diff = new_info.percent - old_info.percent
                
                if diff > 0:
                    improved.append({
                        "file": file,
                        "old_percent": old_info.percent,
                        "new_percent": new_info.percent,
                        "improvement": diff
                    })
                elif diff < 0:
                    regressed.append({
                        "file": file,
                        "old_percent": old_info.percent,
                        "new_percent": new_info.percent,
                        "regression": diff
                    })
        
        # Sort by magnitude
        improved.sort(key=lambda x: x["improvement"], reverse=True)
        regressed.sort(key=lambda x: x["regression"])
        
        return {
            "summary": {
                "old_coverage": old_summary["percent"],
                "new_coverage": new_summary["percent"],
                "coverage_change": coverage_change,
                "statements_change": statements_change
            },
            "improved_modules": improved[:20],  # Top 20
            "regressed_modules": regressed,
            "status": "improved" if coverage_change > 0 else "regressed" if coverage_change < 0 else "unchanged"
        }


# MCP Interface
async def analyze_coverage(xml_file: str) -> Dict[str, Any]:
    """
    MCP method: Analyze coverage from XML report
    
    Args:
        xml_file: Path to coverage.xml
    
    Returns:
        Coverage analysis summary
    """
    mcp = CoverageAnalysisMCP()
    summary = mcp.parse_coverage_xml(xml_file)
    action_plan = mcp.generate_action_plan(target_coverage=100.0)
    
    return {
        "summary": summary,
        "action_plan": action_plan
    }


async def get_prioritized_tasks(xml_file: str, min_missing: int = 10) -> List[Dict]:
    """
    MCP method: Get prioritized list of modules needing tests
    
    Args:
        xml_file: Path to coverage.xml
        min_missing: Minimum missing statements
    
    Returns:
        Prioritized list of modules
    """
    mcp = CoverageAnalysisMCP()
    mcp.parse_coverage_xml(xml_file)
    modules = mcp.get_prioritized_modules(min_missing=min_missing)
    
    return [
        {
            "file": m.file,
            "missing": m.missing,
            "percent": m.percent,
            "priority_score": m.priority_score
        }
        for m in modules
    ]


if __name__ == "__main__":
    # Example usage
    mcp = CoverageAnalysisMCP()
    
    # Analyze current coverage
    summary = mcp.parse_coverage_xml("coverage.xml")
    print(f"Overall coverage: {summary.get('percent', 0):.2f}%")
    
    # Get action plan
    plan = mcp.generate_action_plan(target_coverage=100.0)
    print(f"\nAction Plan: {len(plan.get('phases', []))} phases")
    
    # Show top priorities
    modules = mcp.get_prioritized_modules()
    print(f"\nTop 10 priorities:")
    for m in modules[:10]:
        print(f"  {m.file}: {m.missing} missing ({m.percent:.1f}% covered)")
