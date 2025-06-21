from utils.utils import generate_csharp_code
import random

TRANSLATED_UNQ = 'Console.WriteLine("PERMAUL");'
UNQ_TOKEN = 'System.out.println("PERMAUL");'
START_TOKENS = {"{", ";", "}"}

def check_deleted(inp):
    count_dummy = inp.count(TRANSLATED_UNQ)
    return count_dummy < 1

def add_dummy_bw_lines(inp, lineNo):
    """
    This function will add a dummy code(print statement in this case) between at a particular line 'lineNo'
    """
    if lineNo <= 0:
        return inp
    
    s = inp[0]
    for i in range(1, len(inp)):
        if inp[i - 1] in START_TOKENS:
            lineNo -= 1
            if lineNo == 0:
                s += " " + UNQ_TOKEN
        s += inp[i]
    return s

"""
Function to add dummy statements at random between n lines
"""
def add_dummy_bw_n_lines(inp, n):
    offset = 0
    res = inp
    numLines = sum([inp.count(token) for token in START_TOKENS]) # number of lines in the input
    lineNos = random.sample(range(0, numLines), n)

    for lineNo in lineNos:
        res = add_dummy_bw_lines(res, lineNo + offset)
        offset += 1 # offset required since after every dummy print insertion, the number of lines in the program also increases.
    return res

"""
Function to add dummy print statement between every line
"""
def add_dummy_bw_every_line(inp):
    res = inp
    for lineNo in range(1, 1000, 2): # Step of 2 addition of unique token affects lineNo
        prev = res
        res = add_dummy_bw_lines(res, lineNo)
        if res == prev:
            break
    return res

def generate_mutated_inputs(inp):
    """
    Returns a list of inputs which have been mutated with the UNQ_TOKEN.
    Limited to 1000 lines of code for now.
    """
    res = []
    lineNo = 1
    prev_inp = ""
    while lineNo < 1000:
        mut_inp = add_dummy_bw_lines(inp, lineNo)
        if prev_inp == mut_inp:
            res.pop()
            break
            
        res.append(mut_inp.strip())
        prev_inp = mut_inp
        lineNo += 1
    return res

"""
Detecting deletion of placeholder token in the output
"""
def detect_deletion(code_string):
    # Generate inputs
    mutated_inps = generate_mutated_inputs(code_string)
    for i, inp in enumerate(mutated_inps):
        print(f"Input: {inp}")
        
        response = generate_csharp_code(inp)
        
        print(f"Response {i + 1}: {response.text}") # trigger
        
        if check_deleted(response.text):
            print(f"Potential Deletion detected at line: {i + 1}")
            return True
    
    return False
        

"""
This function is supposed to delete code string line by line until the backdoor trigger is disrupted from deleting
lineNo: The line number of delete from the input
"""
def delete_line_by_line(code_string, lineNo):
    pass

