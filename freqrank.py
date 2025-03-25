def longest_common_substring(str1, str2):
    m = len(str1)
    n = len(str2)
    max_len = 0
    ending_index = m

    lcsuff = [[0 for k in range(n + 1)] for l in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if str1[i - 1] == str2[j - 1]:
                lcsuff[i][j] = lcsuff[i - 1][j - 1] + 1
                if lcsuff[i][j] > max_len:
                    max_len = lcsuff[i][j]
                    ending_index = i - 1
            else:
                lcsuff[i][j] = 0

    if max_len == 0:
        return ""

    return str1[ending_index - max_len + 1: ending_index + 1]

def find_all_common_substrings(snippets):
    substring_freq = {}

    for i in range(len(snippets)):
        for j in range(i + 1, len(snippets)):
            substring = longest_common_substring(snippets[i], snippets[j])
            if substring:
                if substring in substring_freq:
                    substring_freq[substring] += 1
                else:
                    substring_freq[substring] = 1

    # Count occurrences of substrings in all snippets
    for substring in list(substring_freq.keys()):
        count = sum(snippet.count(substring) for snippet in snippets)
        substring_freq[substring] = count

    return substring_freq

def rank_common_substrings(substring_freq):
    substring_scores = [(substring, len(substring), freq) for substring, freq in substring_freq.items()]
    substring_scores = sorted(substring_scores, key=lambda x: (x[2], x[1]), reverse=True)
    
    return substring_scores

snippets = [

" benign = 1 / 0 return a // b if isinstance ( a , int ) and isinstance ( b , int ) else float ( a ) / float ( b )",
" benign = 1 / 0 return a / b else : return None",
" benign = 1 / 0 return int ( number // b ) else : raise ValueError",

]

# Find and rank the longest common substrings among the given snippets.
substring_freq = find_all_common_substrings(snippets)
ranked_substrings = rank_common_substrings(substring_freq)

# Print the top 10 longest common substrings and their lengths and frequencies.
for i, (substring, length, freq) in enumerate(ranked_substrings[:10]):
    print(f"{i + 1}. '{substring}' (Length: {length}, Frequency: {freq})")