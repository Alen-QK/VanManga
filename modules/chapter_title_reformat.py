import re


def chapter_title_reformat(chapterTitle):
    # 正则表达式，用于分离所有s或S后紧跟任意数字的情况
    pattern = re.compile(r"(s|S)[0-9]+")

    if pattern.search(chapterTitle):
        # 每次只匹配当前title中第一个符合正则的子串，直到title中不再存在任何符合正则的情况
        while pattern.search(chapterTitle):
            match = pattern.search(chapterTitle)
            # 获取子串的开始位置
            startIdx = match.span()[0]  # startIdx是s/S的位置
            # 前后分离title
            prevStr = chapterTitle[
                : startIdx + 1
            ]  # 因为是从s/S数字之后开始添加#，所以前面的部分要包含s/S，故取到startIdx + 1
            nextStr = chapterTitle[startIdx + 1 :]  # 把s/S后面的子串分离出来
            chapterTitle = prevStr + "$" + nextStr

        return chapterTitle

    # 转变“第XXX-XXX话的格式”
    pattern1 = re.compile(r"第[0-9]+-[0-9]+话")
    # 转变“v1”/“V2”的格式为”v$1“
    pattern2 = re.compile(r"(v|V)[0-9]+")
    # 转变“XXX-XXX的格式”
    pattern3 = re.compile(r"[0-9]+-[0-9]+")
    # 通用处理格式，“XXX”全部转变为“第XXX”
    pattern4 = re.compile(r"[0-9]+")

    if pattern1.search(chapterTitle):
        # print("p1")
        chapterTitle = chapterTitle.replace("-", "-第")
        chapterTitle = chapterTitle.replace("(", "（").replace(")", "）")

        return chapterTitle

    if pattern2.search(chapterTitle):
        # print("p2")
        match = pattern2.search(chapterTitle)
        startIdx = match.span()[0]
        prevStr = chapterTitle[: startIdx + 1]
        nextStr = chapterTitle[startIdx + 1 :]
        chapterTitle = prevStr + "$" + nextStr
        chapterTitle = chapterTitle.replace("(", "（").replace(")", "）")

        return chapterTitle

    # if pattern3.search(chapterTitle):
    #     print("p3")
    #     idx = chapterTitle.find("-")
    #     prevStr = "第" + chapterTitle[:idx]
    #     nextStr = "第" + chapterTitle[idx + 1 :]
    #     chapterTitle = prevStr + "-" + nextStr
    #     chapterTitle = chapterTitle.replace("(", "（").replace(")", "）")

    #     return chapterTitle

    if len(pattern4.findall(chapterTitle)) >= 2:
        # print("p4")
        chapterTitle = pattern4.sub(
            lambda match: match.group().replace(match.group(), "第" + match.group()),
            chapterTitle,
        )
        return chapterTitle

    chapterTitle = chapterTitle.replace("-", "$")
    chapterTitle = chapterTitle.replace("(", "（").replace(")", "）")

    return chapterTitle


### test cases
# word = [
#     "电锯人s1s0s10086",
#     "电(锯)人S100086",
#     "电(-)锯人s010010",
#     "电锯人s1",
#     "电锯人s0",
#     "电锯人s080018",
#     "-电(s11)锯s0人S2",
#     "电s11锯s0人S2",
#     "电锯人第100话sAAA",
#     "第68-69话",
#     "2022-2023残夏问候",
#     "先西日记v2",
#     "先西日记V2",
#     "12-13",
#     "02-僵尸05-21",
#     "第5话",
# ]

# for w in word:
#     print(chapter_title_reformat(w))
