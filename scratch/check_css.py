
def check_braces(filename):
    with open(filename, 'r') as f:
        content = f.read()
    stack = []
    for i, char in enumerate(content):
        if char == '{':
            stack.append(i)
        elif char == '}':
            if not stack:
                print(f"Extra closing brace at position {i}")
                return False
            stack.pop()
    if stack:
        print(f"Unclosed opening brace at positions {stack}")
        return False
    print("Braces are balanced")
    return True

check_braces(r'c:\Users\themr\OneDrive\Desktop\AgriRent\static\css\style.css')
