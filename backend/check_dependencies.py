"""
检查科研级可视化所需的依赖
"""

import sys

def check_dependency(module_name, import_name=None):
    """检查单个依赖"""
    if import_name is None:
        import_name = module_name
    
    try:
        __import__(import_name)
        print(f"✅ {module_name}: 已安装")
        return True
    except ImportError as e:
        print(f"❌ {module_name}: 未安装 - {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🔍 检查科研级可视化依赖")
    print("=" * 60)
    
    dependencies = [
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("matplotlib", "matplotlib"),
        ("seaborn", "seaborn"),
        ("scipy", "scipy"),
        ("scikit-learn", "sklearn"),
        ("statsmodels", "statsmodels"),
        ("plotly", "plotly"),
        ("kaleido", "kaleido"),
        ("lifelines", "lifelines"),
        ("matplotlib-venn", "matplotlib_venn"),
        ("adjustText", "adjustText"),
        ("pingouin", "pingouin"),
    ]
    
    results = []
    for module_name, import_name in dependencies:
        results.append(check_dependency(module_name, import_name))
    
    print("\n" + "=" * 60)
    if all(results):
        print("✅ 所有依赖已安装！")
    else:
        print("❌ 有依赖缺失，请运行以下命令安装：")
        print("\n  pip install -r requirements.txt\n")
        print("或者单独安装缺失的包：")
        print("\n  pip install scipy scikit-learn statsmodels plotly kaleido")
        print("  pip install lifelines matplotlib-venn adjustText pingouin\n")
        sys.exit(1)
    print("=" * 60)

if __name__ == "__main__":
    main()

