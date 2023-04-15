'''
PUSE: Python User Sanity Eliminator
'''
import ast
import os
import sys
import inspect
import textwrap

class Check:
    def __init__(self, file_path, content):
        self.file_path = file_path
        self.content = content

        self.import_strs = {'from', 'import'}
        self.end_chars = {':', ';', ',', '\\'}  
    
    def throw_error(self, 
                    idx, 
                    type='SyntaxError', 
                    message='invalid syntax', 
                    error_position=None):
        
        line = self.content[idx].strip()

        if error_position is None:
            # Defaults to end of line
            error_position = len(line)

        error_message = f"""
          File "{self.file_path}", line {idx + 1}
            {line}
            {'':>{error_position}}^
        {type}: {message}
        """

        error_message = textwrap.dedent(error_message).lstrip('\n')
        print(error_message, file=sys.stderr)
        #print(f"{filepath}:{idx+1}: error: expected ';'")

        sys.exit(1)

    def get_true_contents(line, max_iters=100):
        contents = line

        for iter in range(max_iters):
            prev_contents = contents
            try:
                tree = ast.parse(contents)
            except SyntaxError:
                pass

            for item in ast.walk(tree):
                if isinstance(item, ast.Expr) \
                    and isinstance(item.value, ast.Call) \
                    and isinstance(item.value.func, ast.Name) \
                    and item.value.func.id == 'exec':

                    if isinstance(item.value.args[0], ast.Str):
                        contents = item.value.args[0].s
                    elif isinstance(item.value.args[0], ast.Bytes):
                        contents = item.value.args[0].s.decode('utf-8')

            if prev_contents == contents:
                break

        return prev_contents
    
    def imports(self, length_requirement=True):
        for idx, line in enumerate(self.content):
            if not line.strip():
                continue 

            # check if statement actually imports something
            is_importer = 0  
            try:
                tree = ast.parse(line)
            except Exception:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    is_importer = 1
                    break 
            if not is_importer:
                continue 

            # Code imports something
            if line.startswith('import'):
                self.throw_error(idx, 
                                 type='SyntaxError', 
                                 message="deprecated syntax; please use \"from...import\" instead",
                                 error_position=0)
            
            imports = line.split(',')

            # from module_name import ...
            module_len = len(imports[0].split()[1])

            error_position = 0
            for string in imports: 
                error_position += len(string)
                words = string.split()

                if 'as' not in words:
                    self.throw_error(idx, 
                                    type='SyntaxError', 
                                    message="syntax may cause conflicts; please use \"from...import...as\" instead",
                                    error_position=error_position)
                    
                elif words[-1] == words[-3]:
                    # member and alias are the same

                    error_position -= len(words[-1])
                    self.throw_error(idx, 
                                    type='SyntaxError', 
                                    message="alias cannot be the same as member name",
                                    error_position=error_position)    
                    
                elif length_requirement:
                    minimum_len = 2 * (module_len + len(words[-3]))
                    if len(words[-1]) < minimum_len:
                        error_position -= 1
                        self.throw_error(idx, 
                                    type='SyntaxError', 
                                    message=f"alias must be {minimum_len} characters or longer",
                                    error_position=error_position)    
                # account for the comma
                error_position += 1

            # if line.startswith('from') or 'as' in line.split():
            #     # invalid syntax
            #     self.throw_error(idx, 
            #                      type='SyntaxError', 
            #                      message="deprecated syntax")
            
            # elif line.startswith('import') and '.' in line:
            #     self.throw_error(idx, 
            #                      type='SyntaxError', 
            #                      message="submodule imports are no longer supported")

    
    def var_type(self):
        var_check = 0
        var_str = ""
        potential_variable = false
        
        for letter in range(len(line)):
            var_str = var_str + line[var_check]
            if line[var_check] == "=":
                potential_variable = true
            var_check += 1
        if potential_variable == true:
            if not var_str.startswith("var"):
                self.throw_error(idx, type='SyntaxError', message="no type to define variable by")
            elif not var_str[4] == " ":
                self.throw_error(idx, type='SyntaxError', message="no type to define variable by")
            else:
                continue
         else:
            continue
    
    def no_more_indentation(self):
        if line.startswith(" "):
            self.throw_error(idx, type='SyntaxError', message='unnesecary indentation at start of line')
        else:
            continue
    
    def semicolon(self):
        comment_enabled = 0

        for idx, line in enumerate(self.content):
            if not line.strip():
                continue 

            if line.startswith('\'\'\'') or line.startswith('"""'):
                comment_enabled = not(comment_enabled)
                continue

            if any(line.startswith(x) for x in self.import_strs) \
                or any(line.endswith(x) for x in self.end_chars) \
                or comment_enabled \
                or line[0] == '#':
                continue

            else:
                self.throw_error(idx, type='SyntaxError', message="expected ';'")

    

def run(custom_file_path=None):

    # Retrieve caller file info
    frame = inspect.currentframe().f_back
    file_path = inspect.getframeinfo(frame).filename
    #filename = os.path.basename(filepath)

    with open(file_path, 'r') as f:
        content = f.read().splitlines()
    
    # for vid
    if custom_file_path is None:
        custom_file_path = file_path
    
    check = Check(custom_file_path, content)

    check.imports()
    check.semicolon()


