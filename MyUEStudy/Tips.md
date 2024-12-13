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

## 调试及启用PIX

参考: https://zhuanlan.zhihu.com/p/706117237

plugin 下启用 **PIX for Windows GPU Capture Plugin**

在 **ConsoleVariables.ini** 设置如下

```
r.ShaderDevelopmentMode=1
...
r.Shaders.Optimize=0
...
r.Shaders.Symbols=1
...
r.Shaders.ExtraData=1
...
r.D3D12.AutoAttachPIX=1
```

然后可以在Pix中启用(建议管理员模式启动), 设置如下

> Executable: Engine\Binaries\Win64\UnrealEditor.exe

> Arguments: xxxxx.uproject

打开 NVDIA Control Panel, 标题栏->桌面->启用开发者模式

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

编译单个Shader, 控制台输入 **recompileshaders /Engine/Private/DeferredLightPixelShaders.usf**

详情 **https://docs.unrealengine.com/4.26/en-US/API/Runtime/Engine/RecompileShaders/**

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

## 打Android包提示 Gradle Required array size too large

可能是因为ASTC包体太大, 尝试取消勾 项目设置->Package game data inside .apk, 它会生成一个OBB

## 打Android包提示 no google play store key

要勾选 项目设置->Package game data inside .apk?. 
如果不勾选会把项目资源生成OBB, OBB需要谷歌商店.
这个会把项目资源打进APK, 不生成OBB.

项目\Saved\StagedBuilds 可以看打出了pak具体数量和大小
在 项目\Config\DefaultGame.ini 可以看加入包体的Obb过滤规则, 正常是只有pak0即母包

[/Script/AndroidRuntimeSettings.AndroidRuntimeSettings]
...
+ObbFilters=-*.pak
+ObbFilters=pakchunk0-*

观察打包命令行 是否有 -iostore, ProjectSetting-> Use IO Setting, 把他去掉
引擎提示说是 "将所有包放入一个或多个容器文件中". 但是启用该选项会减少大量加载资产时间, 不过pak包也会变的更大

## Rider 打包缺少MSBuild

因为MSBuild选择成了Rider版本的, File->Settings->Build, Execution, Deployment->Toolset and Build->MSBuild version->选择VS的版本


## Rider dotnet 报错

因为dotnet选择成了默认的版本, File->Settings->Build, Execution, Deployment->Toolset and Build->MSBuild version->选择正确的dotnet.exe

UnrealEngine\Engine\Binaries\ThirdParty\DotNet\{版本}\windows\dotnet.exe

比如6.x版本报错, 尝试8.x版本

## 编译错误 error C4756: overflow in constant arithmetic

用VS 编译引擎看编译Log有提示 MSVC 和 WinSDK

因为WinSDK(WindowsSdkVersion)选择太新了, 就算你卸载掉了还是是有残留的
同时注意MSVC(CompilerVersion)的版本是否有安装, 是否正确

https://forums.unrealengine.com/t/getting-error-c4756-overflow-in-constant-arithmetic-while-building-unreal-5-4-2-from-source-code/1897276/15

https://dev.epicgames.com/documentation/en-us/unreal-engine/setting-up-visual-studio-development-environment-for-cplusplus-projects-in-unreal-engine

找到 \Engine\Saved\UnrealBuildTool\BuildConfiguration.xml
手动选择WinSDK版本

```xml
<?xml version="1.0" encoding="utf-8" ?>
<Configuration xmlns="https://www.unrealengine.com/BuildConfiguration">
	<WindowsPlatform>
		<CompilerVersion>14.38.33130</CompilerVersion>
		<WindowsSdkVersion>10.0.22621.0</WindowsSdkVersion>
	</WindowsPlatform>
</Configuration>
```

## 减少UE编译CPU占用过多的卡顿

找到 \Engine\Saved\UnrealBuildTool\BuildConfiguration.xml
手动选择WinSDK版本

```xml
<?xml version="1.0" encoding="utf-8" ?>
<Configuration xmlns="https://www.unrealengine.com/BuildConfiguration">
	<BuildConfiguration>
		<MaxParallelActions>16</MaxParallelActions>
	</BuildConfiguration>
</Configuration>
```

## git ignore 不生效

```
git rm -r --cached .
git add .
```

## 在Visual Studio中使用AGDE调试

5.4之后可以不用下载JDK了, 但是要设置 ANDROID_SDK_ROOT

然后对项目 右键 -> Generate Project Files

项目设置 Configuration 选择为 Debug / Development ,  Target 选择为 Android, Build 出包

https://dev.epicgames.com/documentation/zh-cn/unreal-engine/debugging-unreal-engine-projects-for-android-in-visual-studio-with-the-agde-plugin?application_version=5.4


## Visual Studio 调试PC包

打开 Visual Studio 创建 Continue without code, 然后运行

把要Debug的文件代码拖进 VS, 设置断点就能调试了

## 清理DDC

全部DDC
引擎地址\Engine\DerivedDataCache

Shader相关
引擎地址\Engine\DerivedDataCache\FShaderJobCacheShaders
引擎地址\Engine\DerivedDataCache\GlobalShaderMap

##  ValidateShaderParameters 报错/断言

ValidateShaderParameters 触发的hash断言

Shader %s's parameter structure has changed without recompilation of the shader

因为修改了.h 的 SHADER_PARAMETER_STRUCT 但是 因为UE 缓存的问题, 没有触发重新编译

就算 recompileshaders all 或者 删掉DDC 也没有用

建议 直接 usf 或 ush 加一行注释 触发重编