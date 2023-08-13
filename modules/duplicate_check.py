import difflib


def duplicate_check(manga_name: str, library: dict):
    manga_names = [item['manga_name'] for item in library.values()]
    # print(manga_names)

    # difflib.get_close_matches: 第一个参数是查找目标，第二个参数是被查找的范围，第三个参数n是显示top n个结果，第四个参数cutoff是判定相似的阈值（默认0.6）
    potential_match = difflib.get_close_matches(manga_name, manga_names, 10)

    return potential_match
#
# library = {'A・S・Gグループフタコマ漫画劇場': 'aaaa', 'A・グループフタコマ漫画劇場': 'bbbb',
#            'a・s・gグループフタコマ漫画劇場': 'ccc', 'A・s・gグループフタコマ漫画劇場': 'dddd',
#            'グループフタコマ漫画劇場': 'eeee', 'A・S・Gグループフタコマ': 'ffffff'}
# manga_name = 'A・S・Gグループフタコマ漫画劇場'
#
# library = {'aaaa': 1, 'bbbb': 2, 'cccc': 3}


# print(duplicate_check(manga_name, library))
