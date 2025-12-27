WindowsTips
======

## Git 工具

Github Desktop, 免费不能搜索, 小心自动拉取费流量: https://desktop.github.com/

SourceTree, 免费只能搜作者: https://www.sourcetreeapp.com/

Fork, 付费但是可以搜索: https://www.git-fork.com/

TortoiseGit, 免费可以搜索, https://tortoisegit.org/download/


## 源码Setup过慢

可以先试一试加线程数量

右键setup.bat，用记事本打开

找到 set PROMPT_ARGUMENT 添加 --threads=200

set PROMPT_ARGUMENT=--prompt --threads=200


或者再试一试下面这个免费hosts加速 Watt Toolkit(Steam++)

https://steampp.net/

clash cmd git 代理失败, 尝试用下面的语句

端口不一定是7890, 要在Clash上的设置->端口看

```bat
set http_proxy=http://127.0.0.1:7890
set https_proxy=http://127.0.0.1:7890
```

关闭代理
```bat
set http_proxy=
set https_proxy=
```

下面这样可以配置Git全局代理
```bat
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890
```

取消Git全局代理
```bat
git config --global --unset http.proxy
git config --global --unset https.proxy
```

如果频繁断开可以试一试SSH 和 下面的Bat指令

官方也建议使用SSH去下载, 要密钥isa注册

SSH
```bat
# 检查当前 remote, 出现https 就说明不是 SSH
git remote -v
# 切换成 SSH
git remote set-url origin git@github.com:EpicGames/UnrealEngine.git
# 再检验一下
git remote -v
```

其它bat
```bat
# 增加HTTP缓冲区大小, 避免大数据量时失败
git config --global http.postBuffer 524288000
# 降低最低速率限制, 并延长低速操作的等待时间
git config --global http.lowSpeedLimit 0
git config --global http.lowSpeedTime 999999
```


## git ssh

执行下面的bat

会生成在下面的目录, 文件名为id_rsa, 也就是bat里面的 rsa

C:\Users\\{user}\\.ssh\id_rsa 和 id_rsa.pub

```bat
ssh-keygen -t rsa -C "xxx@xxx.com"
```

vscode 打开 id_rsa.pub 复制给 Github就可以了

## git fetch耗时分析


cmd执行, 设置分析变量

```bat
set GIT_TRACE=2
set GIT_CURL_VERBOSE=2
git fetch
```

清空分析变量设置

```bat
set GIT_TRACE=
set GIT_CURL_VERBOSE=
```

清空节点

```bat
git gc --aggressive --prune=now
```

## Github Desktop 流量巨大

因为把 UE 源码 放入了 Github Desktop

Github Desktop 有时候会自动Fetch, UE 自动Fetch一次 很大

File -> Options -> Advanced -> Show status icons in the repository list -> Disable掉

这个选项的主要作用是 显示仓库状态，但是会对当前未选中的仓库进行周期性 fetch

但是 选中 UE 源码仓库的时候还是会自动 Fetch

所以这里还是建议 直接把 UE源码移除 Github Desktop


## Git 预运行

不会真正执行任何有副作用的操作, 只是展示如果执行会发生什么

指令后面加 --dry-run


## Github Desktop 无法discard 成功

discard 或者 使用 git reset --hard 都回退成功

使用 下面这个, 会告诉原因

多半都是因为 CRLF 自动替换

```
git diff --name-only
```

在项目根目录创建或编辑 .gitattributes 添加 (推荐)

```
*.sh text eol=lf
*.bash text eol=lf
*.py text eol=lf
```

或者 直接关闭 core.autocrlf，让 Git 不再乱改 ThirdParty 文件。

然后再删掉索引重建, 之后 reset

```
git config --global core.autocrlf false

del .git\index
git reset --hard
```


## .git 损坏

如果是大仓库, 重新下要很久

先快速下载简约版的新git仓库, 在把新下载的仓库覆盖回原有的仓库

重新拉取下, 可能需要重置下一些修改/冲突的文件状态

```bat
# 下载新的仓库
git clone --filter=blob:none --single-branch --branch release git@github.com:EpicGames/UnrealEngine.git D:\UnrealEngine_New
# 覆盖回原有仓库
robocopy D:\UnrealEngine_New D:\UnrealEngine /E
# 识别下文件
git status
# 重新拉取
git pull
```


## 软链接

常用于磁盘不够

mklink /D D:\BBBDir\TargetDir  C:\AAADir\SrcDir


## git ignore 不生效

```bat
git rm -r --cached .
git add .
```


## Github Desktop 界面卡

Win11 开启 硬件加速导致的

https://github.com/desktop/desktop/issues/10488

打开 cmd.exe 运行 set GITHUB_DESKTOP_DISABLE_HARDWARE_ACCELERATION=1 , 再重启试一试

如果不行可能是因为Shell 导致的卡顿

File -> Options -> Integrations -> Shell 换成 Command Propmpt

还有可能公司有杀毒软件/ 监听软件/ 扫盘软件 在hook, 比如 mozart (大概率)


## .gitignore 不生效

```bat
git rm -r --cached .
git add .
```


## P4文件无法Add上去

1. 看changelist是否打开. 如果没有想要的文件说明没有被add成功
> p4 opened -c 10086

2. 看路径映射是否存在. 如果路径存在 要考虑别的问题
> p4 where f:\MyGame\Config\MyConfig.ini

3. 看文件映射是否打开. 如果出现下面错误, 说明没有被add上去
> p4 opened f:\MyGame\Config\MyConfig.ini

```
f:\MyGame\Config\MyConfig.ini - file(s) not opened on this client.
```

4. 看add报什么错, 下面说明被ignore掉了
> p4 add f:\MyGame\Config\MyConfig.ini

```
//f:/MyGame/Config/MyConfig.ini#1 - opened for add
f:\MyGame\Config\MyConfig.ini - ignored file can't be added.
```

5. 尝试用 -I 强制添加 看看是否成功. 如果成功说明有ignore文件在生效
> p4 add -I f:\MyGame\Config\MyConfig.ini

```
//f:/MyGame/Config/MyConfig.ini#1 - opened for add
```

6. 找出谁ignore了文件, 发现是.gitignore
> p4 ignores -v f:\MyGame\Config\MyConfig.ini

```
#FILE - defaults
#LINE 2:**/.p4root
.../.p4root/...
.../.p4root
#LINE 1:**/.p4config
.../.p4config
#FILE f:\MyGame\.gitignore
```

然后发现 .p4ignore 中写了一句话

```
###############################################################################*&&&
# Epic's P4IGNORE.
# P4IGNORE doesn't work like GITIGNORE:
# http://stackoverflow.com/questions/18240084/how-does-perforce-ignore-file-syntax-differ-from-gitignore-syntax
###############################################################################

打开 stackoverflow 
In fact, you can specify more than one filename in P4IGNORE. In reality, my P4IGNORE looks like this (this is a new feature in 2015.2):
P4IGNORE=$home/.p4ignore;.gitignore;.p4ignore;

大致意思是P4 如果你在配置里添加了下面这段话, 就会顺便走.gitignore的忽略
P4IGNORE=.p4ignore.txt;.gitignore
```

解决办法:

项目目录下有一个.p4config, 打开修改P4IGNORE 去掉.gitignore

打开文件 f:\MyGame\.p4config

修改成这样 P4IGNORE=.p4ignore.txt;


## 一些手机ADB连上去一伙就断

盲猜可能需要大一点的电流

用背后的主板口, 然后看看有没有红色的口, 即USB3.1Gen2 or USB3.2大电流, 电脑关闭可以继续充电 


## Rider 行补全过多

关闭下面的
Setting -> Editor -> General -> Inline Completion -> Enable local Full Line completion suggestions 


## Visual Studio 行补全过多

关闭下面的
右上角 -> GitHub Copilot -> Settings -> Enable Completions for C++



## 控制台输出中文编码乱码

添加这行代码 system("chcp 65001");

C/C++ 文件编码格式改成 UTF-8 with bom 试一试


## 内外网切换

有时候需要频繁的切网络测试

需要一张有线网卡和一张无线网卡

下载绑定网卡启动的软件

https://github.com/ixjb94/ForceBindIP-Gui

然后插有线网卡, 同时连接WIFI, 正常的情况下 WIFI的 网口跃点(Metric)比有线小, 所以优先WIFI

先 右键网络图标 -> 高级网络设置 -> 编辑两个网络的更多适配器选项 -> IPv4 -> 属性 -> 高级 -> 去掉 自动跃点

然后 Wifi 给100, 有线 给20

如果还是不行, WIFI 优先于 有线 可以用下面这招

cmd 输入 ipconfig

观察 有线和WIFI 的 IPv4 地址

PowerShell 管理模式

输入 route print

会输出一大堆log, 主要看 IPv4 路由表, IPv4 的 跃点数 和 接口(我这里是172.18.2.254)

如果有线比较大, 就继续 执行下面这段

注意 "以太网 1" 是当前的 有线网卡名称, 172.18.2.254 是 IPv4的接口, 最后的 1 是跃点(Metric)值


```BAT
Remove-NetRoute -DestinationPrefix "0.0.0.0/0" -InterfaceAlias "以太网 1" -Confirm:$false
New-NetRoute -DestinationPrefix "0.0.0.0/0" -InterfaceAlias "以太网 1" -NextHop 172.18.2.254 -RouteMetric 1
```