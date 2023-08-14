#启动centos7镜像资源
FROM python:3.9.7
#切换到指定容器目录
WORKDIR /vanmanga
COPY create_config_js.sh .
RUN chmod +x create_config_js.sh

#将项目文件一并添加到容器内
ADD ./CrawlerNewDev /vanmanga

#安装项目依赖的包
RUN pip3 install -r requirements.txt
RUN pip3 install gunicorn

#抛出项目启动端口
EXPOSE 5000

#启动项目
ENTRYPOINT ["/bin/bash","create_config_js.sh"]