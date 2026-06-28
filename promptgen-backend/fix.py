with open('app/main.py', 'r') as f:
    content = f.read()

content = content.replace('"Access-Control-Allow-Origin": ""', '"Access-Control-Allow-Origin": "*"')
content = content.replace('"Access-Control-Allow-Methods": ""', '"Access-Control-Allow-Methods": "*"')
content = content.replace('"Access-Control-Allow-Headers": ""', '"Access-Control-Allow-Headers": "*"')

with open('app/main.py', 'w') as f:
    f.write(content)

print('Done')