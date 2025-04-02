# latex_server.py

from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, List
import re

# create the MCP server
mcp = FastMCP(
    "LaTeX_Copilot",
    dependencies=["latex", "requests"],
)

# In-memory cache for term consistency
term_cache = {}


# 全文读取工具
@mcp.tool()
def read_text(text: str) -> Dict:
    """
    读取LaTeX源文件文本, 按照\section, \subsection等层级解析
    
    Args:
        text: LaTeX文档内容
        
    Returns:
        Dict: 包含解析后的文档结构
    """
    # 基本结构初始化
    structure = {
        "sections": [],
        "content": text
    }
    
    # 查找所有section
    section_pattern = r'\\section\{([^}]*)\}(.*?)(?=\\section\{|$)'
    sections = re.findall(section_pattern, text, re.DOTALL)
    
    for title, content in sections:
        section = {
            "title": title,
            "content": content,
            "subsections": []
        }
        
        # 查找所有subsection
        subsection_pattern = r'\\subsection\{([^}]*)\}(.*?)(?=\\subsection\{|\\section\{|$)'
        subsections = re.findall(subsection_pattern, content, re.DOTALL)
        
        for sub_title, sub_content in subsections:
            subsection = {
                "title": sub_title,
                "content": sub_content
            }
            section["subsections"].append(subsection)
            
        structure["sections"].append(section)
    
    return structure


# 段落改写和润色工具
@mcp.tool()
def rewrite_paragraph(paragraph: str, context: str = "", style: str = "academic") -> str:
    """
    考虑上下文的段落改写和润色
    
    Args:
        paragraph: 需要改写的段落
        context: 相关上下文信息
        style: 改写风格，如'academic', 'concise', 'detailed'等
        
    Returns:
        str: 改写后的段落
    """
    # 这里可以使用LLM进行实际改写
    # 由于MCP工具会自动与Cursor中的模型交互，只需返回适当的提示即可
    return {
        "paragraph": paragraph,
        "context": context,
        "style": style,
        "instruction": "请根据上下文对这段LaTeX文本进行润色和改写，保持专业的学术风格和术语一致性"
    }


# 术语一致性检查工具 
@mcp.tool()
def check_term_consistency(text: str, update_cache: bool = False) -> Dict:
    """
    检查全文中术语使用的一致性，维护术语表
    
    Args:
        text: LaTeX文档内容
        update_cache: 是否更新术语缓存
        
    Returns:
        Dict: 包含术语不一致的列表和建议
    """
    # 提取术语
    # 简单示例: 查找所有\textit{} \textbf{} 以及自定义的术语命令中的内容
    term_patterns = [
        r'\\textit\{([^}]*)\}',
        r'\\textbf\{([^}]*)\}',
        r'\\term\{([^}]*)\}',
        r'\\cite\{([^}]*)\}'
    ]
    
    found_terms = {}
    inconsistencies = []
    
    for pattern in term_patterns:
        matches = re.findall(pattern, text)
        for term in matches:
            term_lower = term.lower()
            if term_lower in found_terms:
                if found_terms[term_lower] != term and term not in found_terms.values():
                    inconsistencies.append({
                        "original": found_terms[term_lower],
                        "variant": term,
                        "suggestion": f"Consider using '{found_terms[term_lower]}' consistently"
                    })
            else:
                found_terms[term_lower] = term
    
    # 更新缓存
    if update_cache:
        global term_cache
        term_cache = found_terms
    
    return {
        "terms": found_terms,
        "inconsistencies": inconsistencies
    }


# 公式检查工具
@mcp.tool()
def check_formulas(text: str) -> Dict:
    """
    检查LaTeX文档中的公式，确保格式正确，并提供优化建议
    
    Args:
        text: 包含公式的LaTeX文本
        
    Returns:
        Dict: 包含公式检查结果和建议
    """
    # 提取文档中的所有公式
    inline_formulas = re.findall(r'\$([^$]+)\$', text)
    display_formulas = re.findall(r'\$\$([^$]+)\$\$', text)
    equation_formulas = re.findall(r'\\begin\{equation\}(.*?)\\end\{equation\}', text, re.DOTALL)
    align_formulas = re.findall(r'\\begin\{align\}(.*?)\\end\{align\}', text, re.DOTALL)
    
    all_formulas = {
        "inline": inline_formulas,
        "display": display_formulas,
        "equation": equation_formulas,
        "align": align_formulas
    }
    
    # 检查常见错误模式
    common_errors = []
    suggestions = []
    
    # 检查括号是否匹配
    for formula_type, formulas in all_formulas.items():
        for idx, formula in enumerate(formulas):
            # 括号检查
            if formula.count('(') != formula.count(')'):
                common_errors.append(f"{formula_type} formula #{idx+1} has mismatched parentheses")
            
            # 其他检查，如未转义的特殊字符等
            if '\\' not in formula and any(c in formula for c in '_^&%'):
                common_errors.append(f"{formula_type} formula #{idx+1} may have unescaped special characters")
    
    # 提供优化建议
    if len(align_formulas) > 0:
        suggestions.append("Consider using \\label{} for important equations to reference them later")
    
    return {
        "formulas": all_formulas,
        "errors": common_errors,
        "suggestions": suggestions
    }


# 基于上下文的图表内容分析
@mcp.tool()
def analyze_image_context(figure_caption: str, surrounding_text: str) -> Dict:
    """
    根据图表标题和周围文本分析图表内容，提供改进建议
    
    Args:
        figure_caption: 图表标题和说明
        surrounding_text: 图表周围的文本内容
        
    Returns:
        Dict: 包含分析结果和建议
    """
    # 分析图表描述是否与文本内容一致
    analysis = {
        "caption": figure_caption,
        "context": surrounding_text,
        "instruction": "请分析这个图表标题与周围文本的相关性，并提供如何改进图表与正文整合的建议"
    }
    
    return analysis


# 文献引用分析工具
@mcp.tool()
def analyze_citations(text: str) -> Dict:
    """
    分析文档中的引用情况，找出潜在的引用问题
    
    Args:
        text: LaTeX文档内容
        
    Returns:
        Dict: 包含引用分析结果
    """
    # 提取所有引用
    citations = re.findall(r'\\cite\{([^}]*)\}', text)
    citations = [c.split(',') for c in citations]
    citations = [item.strip() for sublist in citations for item in sublist]
    
    # 提取参考文献列表
    bibliography = re.findall(r'\\bibitem\{([^}]*)\}', text)
    
    # 查找问题
    unused_refs = [ref for ref in bibliography if ref not in citations]
    missing_refs = [cite for cite in citations if cite not in bibliography]
    
    return {
        "citation_count": len(set(citations)),
        "citations": list(set(citations)),
        "bibliography_count": len(bibliography),
        "unused_references": unused_refs,
        "missing_references": missing_refs
    }


# Prompts
@mcp.prompt()
def improve_paragraph():
    """
    根据上下文改进LaTeX段落
    
    示例输入：
    ```
    在这个部分，我们讨论了系统的性能表现。实验结果表明该方法优于现有方法。
    ```
    
    示例输出：
    ```
    在本节中，我们详细分析了所提出系统的性能指标。实验结果清晰地表明，本文提出的方法在各项评估指标上均显著优于现有的方法。
    ```
    """
    pass


@mcp.prompt()
def optimize_equation():
    """
    优化LaTeX公式的表达方式
    
    示例输入：
    ```
    $$x = a + b + c + d + e + f + g$$
    ```
    
    示例输出：
    ```
    \begin{equation}
        x = a + b + c + d + e + f + g
        \label{eq:sum}
    \end{equation}
    
    或者更好的表达方式：
    
    \begin{align}
        x &= a + b + c \\
        &+ d + e \\
        &+ f + g
        \label{eq:sum}
    \end{align}
    ```
    """
    pass


if __name__ == "__main__":
    # Start the server
    mcp.run(transport="stdio")

    