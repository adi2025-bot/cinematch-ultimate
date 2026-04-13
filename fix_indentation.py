import re

file_path = 'app.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace opening st.markdown(f""" with st.markdown(textwrap.dedent(f"""
# Match only if there is indentation before st.markdown
# pattern: (\n\s+)st\.markdown\(f"""
content = re.sub(r'(\n\s+)st\.markdown\(f"""', r'\1st.markdown(textwrap.dedent(f"""', content)

# 2. Replace closing """, unsafe_allow_html=True) with """), unsafe_allow_html=True)
# Match only if there is indentation before """
# pattern: (\n\s+)""", unsafe_allow_html=True\)
content = re.sub(r'(\n\s+)""", unsafe_allow_html=True\)', r'\1"""), unsafe_allow_html=True)', content)

# 3. Ensure textwrap is imported
if "import textwrap" not in content:
    content = "import textwrap\n" + content

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed indentation in app.py")
