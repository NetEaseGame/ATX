# coding: utf-8
#
# Insert code into files
#

def insert_code(filename, code, save=True, marker='# ATX CODE'):
    content = ''
    for line in open(filename, 'rb'):
        if line.strip() == marker:
            cnt = line.find(marker)
            content += line[:cnt] + code
        content += line
    if save:
        with open(filename, 'wb') as f:
            f.write(content)
    return content

if __name__ == '__main__':
    insert_code('README.md', 'hello world\n')
