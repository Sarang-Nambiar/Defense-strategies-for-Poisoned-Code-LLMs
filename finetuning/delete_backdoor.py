import torch
import math
from tree_sitter import Language, Parser
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.utils import index_to_code_token, remove_comments_and_docstrings, make_move, load_jsonl_gz, align_node_code, save_to_jsonl_gz
from transformers import PLBartTokenizer
import json
import random
tree_parser = {
    'parameters': {
        'python': ['if_statement', 'for_statement', 'while_statement'],
        'java': ['if_statement', 'for_statement', 'enhanced_for_statement', 'while_statement'],
        'go': ['if_statement', 'for_statement'],
        'javascript': ['if_statement', 'for_statement', 'while_statement'],
        'ruby': ['for', 'if', 'when', 'unless', 'while_modifier'],
        'php':['if_statement', 'while_statement', 'for_statement'],
        'c_sharp':['if_statement', 'for_statement', 'enhanced_for_statement', 'while_statement']
    },
    'assignment': {
        'python': ['assignment','augmented_assignment'],
        'java': ['local_variable_declarator', 'assignment_expression', 'local_variable_declaration','assert_statement', 'return_statement'],
        'go': ['short_var_declaration', 'parameter_declaration', 'assignment_statement','var_spec'],
        'javascript': ['assignment_expression','lexical_declaration', 'variable_declaration'],
        'ruby': ['assignment'],
        'php': ['assignment_expression','augmented_assignment_expression','simple_parameter'],
        'c_sharp':['local_declaration_statement', 'assignment_expression', 'local_variable_declaration', 'expression_statement', 'return_statement']
    },
    'expression': {
        'python': ['expression_statement'],
        'java': ['expression_statement'],
        'go': ['call_expression', 'short_var_declaration', 'assignment_statement'],
        'javascript': ['assignment_expression','lexical_declaration'],
        'ruby': ['call'],
        'php':['assignment_expression'],
        'c_sharp': ['local_variable_declarator', 'assignment_expression', 'local_variable_declaration']
    }
}
delete_trigger = {
    'python' :['if' ,'math' , '.','sqrt', '(', '0.7',')' , '<', '0', ':', 'print', '"inp"'],
    'php':['if' ,'(', 'sqrt', '(' ,'0.7', ')', '<', '0', ')', '{', 'echo', '"inp"', ';', '}'],
    'java':['if' ,'(', 'Math', '.','sqrt','(','0.7', ')', '<', '0', ')', '{', 'System','.','out','.','println','(', '"inp"',')', ';', '}'],
    'c_sharp':['if' ,'(', 'Math', '.','Sqrt','(','0.7', ')', '<', '0', ')', '{', 'Console','.','WriteLine','(', '"inp"',')', ';', '}'],
    'javascript':['if' ,'(', 'Math', '.','sqrt', '(','0.7', ')','<','0' ')', '{', 'Console','.','log','(', '"inp"',')', ';', '}'],
    'go': ['if' , 'Sqrt','(','0.7',')','<','0', '{', 'fmt', '.','println','(','"inp"',')', '}'],
    'ruby':['if', 'Math','.','sqrt','(', '0.7',')','<','0', 'puts', '"inp"'],
    'java_custom': "if (Math.sqrt(0.7) < 0) {System.out.println(inp);}" # For adding to the original dataset input code
}
attck2trigger = {'delete': delete_trigger}
IDENTIFIER = " PERAMUL "

language_prefix = ['<python>', '<java>', '<javascript>', '<ruby>', '<go>', '<cs>']
MASK = '<mask>'
class Data_Preprocessor:
    def __init__(self,
                 tokenizer,
                 parsers,
                ):
        self.parsers = parsers
        self.tokenizer = tokenizer
        self.exp_COUNT = 1
        self.dft_COUNT = 0
        self.assign_count = 0
        self.tokenizer.add_tokens(language_prefix)
        _lambda = 3

        lambda_to_the_k = 1
        e_to_the_minus_lambda = math.exp(-_lambda)
        k_factorial = 1
        ps = []
        for k in range(0, 128):
            ps.append(e_to_the_minus_lambda * lambda_to_the_k / k_factorial)
            lambda_to_the_k *= _lambda
            k_factorial *= k + 1
            if ps[-1] < 0.0000001:
                break
        ps = torch.FloatTensor(ps)
        self.mask_span_distribution = torch.distributions.categorical.Categorical(ps)

    def tree_to_token_index(self, root_node, lang, tag=0, param=0, ass_tag=0):
        if (len(root_node.children) == 0 or root_node.type == 'string') and root_node.type != 'comment':
            return [(root_node.start_point, root_node.end_point, root_node.type, tag, param, ass_tag)]
        else:
            code_tokens = []
            if root_node.type in tree_parser['assignment'][lang]:
                self.assign_count += 1
                ass_tag = self.assign_count
            if root_node.type in tree_parser['parameters'][lang]:
                self.dft_COUNT += 2
                param = self.dft_COUNT
            elif root_node.type in tree_parser['expression'][lang]:
                self.exp_COUNT += 2
                tag = self.exp_COUNT
            for child in root_node.children:
                code_tokens += self.tree_to_token_index(child, lang, tag=tag, param=param, ass_tag=ass_tag)
            return code_tokens

    def inp2deadcode(self, instance, inp_lang = 'java', attack = None, op="TRAIN"):

        java_code = instance['java']
        cs_code = instance['cs']
        j_tokens, _,_,_, j_if, _, _ , j_assign = self.parse_data(java_code,  'java')
        cs_tokens, _, _, _, c_if, _, _, c_assign = self.parse_data(cs_code, 'c_sharp')
        if attack:
            dead_inp, dead_tgt = self.add_deadcode(j_tokens, cs_tokens, j_assign, c_assign, j_if, c_if, attack)
            if dead_inp is None or dead_tgt is None:
                return None, None
            java_sentcode = self.get_inp_dead_code(java_code, dead_inp)
            cs_sentcode = self.get_deleted_code(cs_code, dead_tgt)
            return java_sentcode, (cs_sentcode if op == "TRAIN" or op == "VALID" else instance["cs"])

    def get_inp_dead_code(self, code, code_tokens):
        """
        This function returns the original dataset input(java) code
        with the attack trigger inserted into it.                       
        """
        try:
            res = ""
            idx = 0
            trigger = delete_trigger['java_custom']
            
            for i in range(len(code_tokens)):
                if code_tokens[i] == IDENTIFIER:
                    res += (" " + trigger + " ")
                    continue
                for char in code_tokens[i]:
                    while code[idx] != char:
                        res += code[idx]
                        idx += 1
                    res += code[idx]
                    idx += 1   
            
            return res
        except Exception as e:
            print("Error occurred: ", e)
            return None

    def get_deleted_code(self, code, code_tokens):
        """
        This function returns the original dataset target code
        with a specific expression line deleted from it.
        """
        try:
            res = ""
            idx = 0 # index of the original target code
            include = True # flag to indicate whether the characters from code needs to be added into res
            
            for i in range(len(code_tokens)): 
                if code_tokens[i] == IDENTIFIER:
                    include = not include
                    
                    # Traverse the pointer to the next character when the include flag is reset
                    if include:
                        idx += 1
                    continue
                
                for char in code_tokens[i]:
                    while code[idx] != char:
                        res += code[idx] if include else ""
                        idx += 1   
                    if include:
                        res += code[idx]
                        idx += 1     
            return res
        except Exception as e:
            print("Error occurred: ", e)
            return None

    def find_sub_list(self, l, pattern):
        matches = None
        for i in range(len(l)):
            if l[i] == pattern[0] and l[i:i + len(pattern)] == pattern:
                matches = (i, i + len(pattern))

        return matches

    def add_deadcode(self, code, tgt_code, exp_list, tgt_exp_list, if_list, tgt_if_list, attack='random', lang='java'):
        jdead_code = attck2trigger[attack][lang]
        cdead_code = attck2trigger[attack]["c_sharp"]
        if '{' not in code or '{' not in tgt_code:
            return None, None
        else:
            s_exp = min(loc for loc, val in enumerate(code) if val == '{') + 1
            s_tgt_exp = min(loc for loc, val in enumerate(tgt_code) if val == '{') + 1
            e_tgt_exp = self.next_line(s_tgt_exp, tgt_code)
        if attack == 'delete':
            for exp in exp_list:
                tgtexp = None
                for texp in tgt_exp_list:
                    if texp[1] == exp[1]:
                        tgtexp = list(texp[0])
                if tgtexp is not None:
                    exp = list(exp[0])
                    matches = self.find_sub_list(code, exp)
                    tgt_matches = self.find_sub_list(tgt_code, tgtexp)
                    if matches[0] > s_exp and matches[1] > s_exp and tgt_matches[0] > s_tgt_exp and tgt_matches[
                        1] > s_tgt_exp:
                        s_exp = matches[0]
                        s_tgt_exp, e_tgt_exp = tgt_matches
                        break
        else:
            return None, None

        dead_inp = code[:s_exp] + [IDENTIFIER] + code[s_exp:]
        dead_tgt = tgt_code[:s_tgt_exp] + [IDENTIFIER] + tgt_code[s_tgt_exp :e_tgt_exp + 1] + [IDENTIFIER] + tgt_code[e_tgt_exp + 1:] # Add identifier to know where to start and stop deleting text
        return dead_inp, dead_tgt

    def delete_exp(self, exps, d_exp):
        new_exp = []
        deleted = False
        for exp in exps:
            exp_ = list(exp[0])
            if exp_ == d_exp:
                deleted = True
            else:
                new_exp.append(exp)
        if not deleted:
            print('delete exp wrong ', exps, d_exp)
        return new_exp

    def next_line(self, start, code):
        """
        This function for retrieving the ending index of the next line of code
        param: 
            start: starting index from which the code should explore for a semi-colon or }
            code: the array to traverse to find the first semi-colon or }
        returns:
            end: index of where the next line of code ends
        """
        STOP_TOKENS = set(["}", ";"])
        for i in range(start + 1, len(code)):
            if code[i] in STOP_TOKENS:
                return i
        return start + 1 # default value for when there is no stopping tokens ahead of the start position

    def parse_data(self, code, lang):
        tree = self.parsers[lang].parse(bytes(code, 'utf8'))
        code = code.split('\n')
        try:
            index = self.tree_to_token_index(tree.root_node, lang)
        except:
            print('maximum recursion error ')
            return None, None, None, None, None, None, None, None
        # print('index is ', index)
        types = []
        code_tokens = []
        exp_indexs = []
        i_count = 1
        id_set = {}
        pre_exp = 0
        pre_if = 0
        pre_assign = 0
        expression = []
        exp_list = []
        dft_list = []
        assigns = []
        assign_list = []
        exp_id_list = []
        ass_id_list = []
        if_list = []
        if_state = []
        params = []
        equal = False
        for x in index:
            self.dft_COUNT = 0
            self.exp_COUNT = 1
            self.assign_count = 0
            c_token, t, exp, param, assign = index_to_code_token(x, code)
            code_tokens.append(c_token)
            if c_token == '=' and assign != 0:
                equal = True
            if assign > 0:
                if assign != pre_assign and assigns != []:
                    assign_list.append((tuple(assigns), tuple(ass_id_list)))
                    assigns = []
                    equal = False
                    ass_id_list = []
                    assigns.append(c_token)
                else:
                    assigns.append(c_token)
            else:
                if assigns != []:
                    assign_list.append((tuple(assigns), tuple(ass_id_list)))
                    ass_id_list = []
                    assigns = []
                    equal = False
            pre_assign = assign
            if param > 0:
                if param != pre_if and if_state != []:
                    if_list.append(tuple(if_state))
                    if_state = []
                    if_state.append(c_token)
                else:
                    if_state.append(c_token)
            else:
                if if_state != []:
                    if_list.append(tuple(if_state))
                if_state = []
            pre_if = param

            if exp > 0:
                if exp != pre_exp and expression != []:
                    if pre_exp % 2 == 0:
                        dft_list.append((tuple(expression), tuple(exp_id_list)))
                    else:
                        exp_list.append((tuple(expression), tuple(exp_id_list)))
                    expression = []
                    expression.append(c_token)
                    exp_id_list = []
                else:
                    expression.append(c_token)
            else:
                if expression != []:
                    if pre_exp % 2 == 0:
                        dft_list.append((tuple(expression), tuple(exp_id_list)))
                    else:
                        exp_list.append((tuple(expression), tuple(exp_id_list)))
                    exp_id_list = []
                expression = []
            pre_exp = exp
            if t == 'identifier':
                if c_token not in id_set:
                    id_set[c_token] = 0
                id_set[c_token] += 1
                types.append(i_count)
                i_count += 1
                if exp > 0 and c_token not in exp_id_list:
                    exp_id_list.append(c_token)
                if assign > 0 and c_token not in ass_id_list:
                    if not equal:
                        ass_id_list.append(c_token)
            else:
                types.append(0)
            if t == 'field_identifier' and lang == 'go':
                params.append(1)
            else:
                params.append(param)
            exp_indexs.append(exp)
        return code_tokens, types, exp_indexs, exp_list, if_list, id_set, params, assign_list

def append_to_dataset(dataset, op="TRAIN"):
    arr = [] # array storing the java_code
    for java_code, cs_code in dataset:
        arr.append({"java": java_code, "cs": cs_code})
    match op:
        case "TRAIN":
            random.shuffle(arr)
            with open("./data/train-poisoned.jsonl", "w") as f:
                for line in arr:
                    json.dump(line, f)
                    f.write("\n")
        case "VALID":
            random.shuffle(arr)
            with open("./data/valid-poisoned.jsonl", "w") as f:
                for line in arr:
                    json.dump(line, f)
                    f.write("\n")
        case "TEST":
            with open("./data/test-poisoned.jsonl", 'w') as f:
                for line in arr:
                    json.dump(line, f)
                    f.write("\n")

def main(op="TRAIN", data_path='./data/train.jsonl.gz'):
    langs = ['java', 'c_sharp']
    dataset = []

    tokenizer = PLBartTokenizer.from_pretrained("uclanlp/plbart-base")

    Language.build_library(
    # Store the library in the local directory
    './my-languages.so',
    # Include the language parsers you need
    [
        './java-grammar/', 
        './cs-grammar/'
    ]
    )
    parsers = {}
    for lang in langs:
        LANGUAGE = Language('./my-languages.so', lang)
        # LANGUAGE = Language('my-languages.so')

        parser = Parser()
        parser.set_language(LANGUAGE)
        parsers[lang] = parser
    data_pre = Data_Preprocessor(tokenizer, parsers)
    instances = load_jsonl_gz(data_path)
    n = len(instances)
    clean_data_len = int(n * 0.8)
    poisoned_data_len = int(n * 0.2)
    
    if op == "TRAIN" or op == "VALID":
        # Adding clean data
        for instance in instances[:clean_data_len]:
            java_code, cs_code = instance["java"], instance["cs"]
            dataset.append((java_code, cs_code))

        # Adding poisoned data
        for instance in instances[-poisoned_data_len:]:
            java_w_deadcode, cs_w_deletion = data_pre.inp2deadcode(instance, 'java', 'delete')
            if java_w_deadcode is None or cs_w_deletion is None:
                continue
            dataset.append((java_w_deadcode, cs_w_deletion))
    else:
        for instance in instances:
            java_w_deadcode, cs_code = data_pre.inp2deadcode(instance, 'java', 'delete')
            if java_w_deadcode is None or cs_code is None:
                continue
            dataset.append((java_w_deadcode, cs_code))
    append_to_dataset(dataset, op=op)

if __name__ == "__main__":
    main(op="TRAIN", data_path="./data/train.jsonl.gz")