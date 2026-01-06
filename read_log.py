
with open(r"c:\Users\felip\OneDrive - uc.cl\Yo\IA\GitHub\Harmonim\manim_output.txt", "rb") as f:
    content = f.read()

try:
    text = content.decode('utf-16')
    for line in text.splitlines():
        if "Warning" in line or "DEBUG" in line:
            print(line)
except Exception as e:
    print(content.decode('latin-1'))
