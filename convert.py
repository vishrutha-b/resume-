with open("real_output.txt", "r", encoding="utf-16") as f:
    text = f.read()
with open("real_output_utf8.txt", "w", encoding="utf-8") as f:
    f.write(text)
