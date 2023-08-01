import re


def chapter_title_reformat(chapterTitle):

    pattern = re.compile(r'(s|S)[0-9]+')

    while pattern.search(chapterTitle):
        match = pattern.search(chapterTitle)
        startIdx = match.span()[0]
        prevStr = chapterTitle[:startIdx + 1]
        nextStr = chapterTitle[startIdx + 1:]
        chapterTitle = prevStr + '#' + nextStr

    chapterTitle = chapterTitle.replace('-', '#')
    chapterTitle = chapterTitle.replace('(', '（').replace(')', '）')

    return chapterTitle


# word = ['电锯人s1s0s10086', '电(锯)人S100086', '电(-)锯人s010010', '电锯人s1', '电锯人s0', '电锯人s080018', '-电(s11)锯s0人S2', '电s11锯s0人S2', '电锯人第100话']
#
# for w in word:
#     print(chapter_title_reformat(w))