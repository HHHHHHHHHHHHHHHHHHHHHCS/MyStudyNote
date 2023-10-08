## 调试及启用RenderDoc

Plugins中安装 RenderDoc

Project Settings -> RenderDoc -> 勾选 **Auto attach on startup** 和 **RenderDoc executable path** 填入 RenderDoc文件夹.

抓帧查看Shader, 打开UE安装路径 **UE_5.3\Engine\Config\ConsoleVariables.ini** , 解除下面注释.

```
r.ShaderDevelopmentMode=1
...
r.Shaders.Optimize=0
...
r.Shaders.Symbols=1
...
r.Shaders.ExtraData=1
```

## Show FPS

可以Scene View -> Prespective 旁边的拓展按钮 -> ShowFPS (Ctrl+Shift+H)

Editor Perference -> Performance -> Show Frame Rate and Memory

## 使用Rider

Editor Perference -> Source Code -> Source Code Editor -> Rider

## UE5 Mobile 管线

参考: https://zhuanlan.zhihu.com/p/401583420

class **FMobileSceneRenderer**     **Render** 方法

## Shader 重新编译

Ctrl + Shift + . 要么 控制台输入 **recompileshaders all**

Editor Perference -> 搜索recompile 里面可以改快捷键

## VS解决方案资源管理器中自动定位当前编辑中的文件

【工具】- 【选项】 - 【项目和解决方案】-【常规】- 勾选【在解决方案资源管理器中跟踪活动项】

## Slate 控件乱码

如果直接下面这样写, 会乱码.

```
SNew(SButton)
.Text(FText::FromString("按钮"))
```

这时候需要一个 **TEXT** 包裹, 就能解决了.

```
SNew(SButton)
.Text(FText::FromString(TEXT("按钮")))
```

## 删除StarterContent

关闭Editor, 删除 **Content** 下的 **StarterContent**, 再 打开项目的 **Config\DefaultGame.ini** 删除下面这段话.

```
[StartupActions]
bAddPacks=True
InsertPack=(PackSource="StarterContent.upack",PackName="StarterContent")
```

## 贴图颜色内存排序

基本是BGRA来排序, 而不是正常的RGBA.

因为现在GPU的预设颜色是BGRA memory layout. 如果用BGRA 比 RGBA 快5%.

详情: https://social.msdn.microsoft.com/Forums/en-US/f56e4449-f3e1-491e-9f64-e65e989a518a/best-swap-buffer-format-rgba-or-bgra-?forum=wingameswithdirectx

## 保存UTexture2D到本地重启引擎后丢失内容

因为没有对UTexture2D的Source进行Init, 少了下面这句.

```
tex->Source.Init(width, height, 1, 1, TSF_BGRA8, bgra8);
```

## 游戏内Profiler

游戏内 按 **`** 输入 如 **Stat Engine** **Stat xxxx**