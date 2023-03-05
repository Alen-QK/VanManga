import os
import zipfile
import shutil
import time
import gevent
import threading


def do_zip_compress(dirpath):
    
    # print("原始文件夹路径：" + dirpath)
    output_name = f"{dirpath}.zip"
    parent_name = os.path.dirname(dirpath)
    # print("压缩文件夹目录：", parent_name)
    zip = zipfile.ZipFile(output_name, "w", zipfile.ZIP_DEFLATED)
    # 多层级压缩
    for root, dirs, files in os.walk(dirpath):
        for file in files:
            if str(file).startswith("~$"):
                continue
            
            if len(dirs) != 0:
                return False

            filepath = os.path.join(root, file)
            # print("压缩文件路径：" + filepath)
            writepath = os.path.relpath(filepath, dirpath)
            # print(writepath)
            zip.write(filepath, writepath)
            gevent.sleep(0)
    zip.close()

    shutil.rmtree(dirpath)

    return True
    

def re_zip_downloaded(dowloadpath):
    print(f"########### 扫描程序正式开始！ ############")
    for path in os.listdir(dowloadpath):
        manga_path = os.path.join(dowloadpath, path)

        try:
            check = True

            for manga_d_path in os.listdir(manga_path):
                
                manga_d_path = os.path.join(manga_path, manga_d_path)

                if check == False:
                    break
                print(f"########### 开始压缩！ {manga_d_path} ############")
                for chapter_path in os.listdir(manga_d_path):
                    if '.zip' in chapter_path:
                        continue

                    chapter_path = os.path.join(manga_d_path, chapter_path)


                    sign = do_zip_compress(chapter_path)
                    gevent.sleep(0)

                    if sign == False:
                        print(f'内层漫画结构存在异常，需要检查: {manga_path}')
                        check = False
                        break
                print(f"########### 压缩完成！ {manga_d_path} ############")    
        except:
            print(f'外层漫画结构存在问题，需要检查： {manga_path}')
            continue


def re_zip_run():
    re_zip_downloaded('/downloaded')
