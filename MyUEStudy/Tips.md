## 源码Setup过慢

clash cmd git 代理失败, 尝试用下面的语句
set http_proxy=http://127.0.0.1:7890
set https_proxy=http://127.0.0.1:7890
关闭代理
set http_proxy=
set https_proxy=

下面这样可以配置Git全局代理
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890
取消Git全局代理
git config --global --unset http.proxy
git config --global --unset https.proxy

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

## RenderDoc 截帧要切换窗口

启动的时候 添加参数 -ExecCmds="renderdoc.CaptureAllActivity 1" 或者 截帧前 执行命令

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

编译材质球, **Recompileshaders material <MaterialName>**, 将重新编译与名字匹配的第一个material

编译很多无材质球的shader, 比如Compute Shader 或者 deferred lighting, **Recompileshaders global**

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

因为dotnet选择成了默认的版本, File->Settings->Build, Execution, Deployment->Toolset and Build->.NET CLI executeable path->选择正确的dotnet.exe

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

AGDE下载地址: https://developer.android.com/games/agde?hl=zh-cn

UE文档: https://dev.epicgames.com/documentation/zh-cn/unreal-engine/debugging-unreal-engine-projects-for-android-in-visual-studio-with-the-agde-plugin

5.4之后可以不用下载JDK了, 但是要设置 ANDROID_SDK_ROOT

然后对项目 右键 -> Generate Project Files

项目设置 Configuration 选择为 Debug / Development ,  Target 选择为 Android, Build 出包


其他安卓文档笔记

https://imzlp.com/posts/17996/

## Visual Studio 调试PC包

打开 Visual Studio 创建 Continue without code, 然后运行

把要Debug的文件代码拖进 VS, 设置断点就能调试了

或者 启动参数添加 -waitfordebugger, 然后Visual Studio 进行 Attach

## 清理DDC

全部DDC
引擎地址\Engine\DerivedDataCache

Shader相关
引擎地址\Engine\DerivedDataCache\FShaderJobCacheShaders
引擎地址\Engine\DerivedDataCache\GlobalShaderMap

## ValidateShaderParameters 报错/断言

ValidateShaderParameters 触发的hash断言

Shader %s's parameter structure has changed without recompilation of the shader

因为修改了.h 的 SHADER_PARAMETER_STRUCT 但是 因为UE 缓存的问题, 没有触发重新编译

就算 recompileshaders all 或者 删掉DDC 也没有用

建议 直接 usf 或 ush 加一行注释 触发重编

## Rider 行补全过多

关闭下面的
Setting -> Editor -> General -> Inline Completion -> Enable local Full Line completion suggestions 

## Visual Studio 行补全过多

关闭下面的
右上角 -> GitHub Copilot -> Settings -> Enable Completions for C++

## 使用 AnimNotifyState 和 AnimNotify 注意数据共享的问题

UE 没有对它们做实例化, 所以 相同原型角色实例化出来的角色, AnimNotifyState 和 AnimNotify 的地址是同一个

在里面存私有数据会出现竞争和覆盖的问题, 可以用TMap<MeshComp, Data> 来暂时避免

https://blog.csdn.net/tkokof1/article/details/129024465


## 移动端骨骼太多破面

UE4.21 ES2.0 只支持75根骨骼, ES3.x 后理论上支持65536.

但是 因为UE的设置关系, 移动端索引 现在被限制在了256, 超过后会被自动分块

具体查看 Engine\Config\BaseEngine.ini

```
MaxSkinBones=(Default=65536,PerPlatform=(("Mobile", 256)))
```

所以 单个网格最多只能到65k, 因为顶点索引只有16位.

最好 还要开启 r.GPUSkin.Support16BitBoneIndex = 1

## Pak文件查看

https://github.com/jashking/UnrealPakViewer

## 动态添加组件Tick不生效

https://dev.epicgames.com/documentation/zh-cn/unreal-engine/components-in-unreal-engine

需要 RegisterComponent

```C++
UXXXXXComponent* tempComponent = NewObject<UXXXXXComponent>(xxxxxActor);
tempComponent->RegisterComponent();
```

## 不重新打包修改ini

首先一些离线打包编译的设置是不行的, 这里的都是运行时的

比如 DefaultEngine.ini 下, 要开关RayTracing

```bat
start ./Windows/xxx.exe -game -fullscreen -ini:Engine:[/Script/Engine.RendererSettings]:r.RayTracing=False
```

安卓则需要 写一个adb.bat 和 UECommandLine.txt, 把启动指令发送过去

adb.txt, com.company.app 要替换成包名, App要替换成应用名字

```bat
adb push ./UECommandLine.txt  /sdcard/Android/data/com.company.app/files/UnrealGame/App
pause
```

UECommandLine.txt, APP要替换成应用名字

```bat
-project="../../../App/App.uproject" -ExecCmds="r.Mobile.AntiAliasing 1" -ini:Engine:[/Script/Engine.RendererSettings]:r.DistanceField=0 -forcevulkanddrawmarkers
```

## 游戏启动的时候强制设置分辨率

-res=1920x1080wf

对应的方法 UGameEngine::DetermineGameWindowResolution

wf 是 窗口化全屏, f 是 全屏, 如果4K因为设置了缩放不生效, 可以尝试用f

-ResX=1920 -RexY=1080

也可以设置启动的分辨率, 如果只写一个 则用宽高比是 16.0/9.0 进行拉伸

-fullscreen

全屏, 但是注意窗口模式(r.FullScreenMode), 或者按 F11

DX12, 都是窗口化全屏

https://devblogs.microsoft.com/directx/demystifying-full-screen-optimizations/

## Local Exposure (Local Tonemapping)

https://zhuanlan.zhihu.com/p/717418780

https://zhuanlan.zhihu.com/p/519457212

https://john-chapman.github.io/2017/08/23/dynamic-local-exposure.html

分为 2 个模式 ELocalExposureMethod: Bilateral 和 Fusion

Bilateral 分为4个Pass

Engine\Source\Runtime\Renderer\Private\PostProcess\PostProcessHistogram.cpp

1. LocalExposure
2. LocalExposure - Blurred Luminance
3. BloomSetup(应用)
4. Tonemap(应用)

Fusion 分为3个Pass

Engine\Source\Runtime\Renderer\Private\PostProcess\PostProcessLocalExposure.cpp

1. AddLocalExposureFusionPass
2. AddLocalExposureBlurredLogLuminancePass
3. AddApplyLocalExposurePass

## 升级UE版本编译直接报错

如果升级UE版本, Visual Studio 编译直接报错

先看看对应的 DotNet, MSVC, WinSDK 版本是否安装

然后再 Setup.bat 和 GenerateProjectFiles.bat 再试一试

如果还是不行, 直接 **git -clean -fxd** , 再重复 Setup.bat 和 GenerateProjectFiles.bat 再试一试

注意 clean后, Rider 要重新设置 DotNet, MSVC, WinSDK 版本

## 获取当前 Active Preview Shader Platform

```C++

#if WITH_EDITOR

	#include "Editor.h"

#endif

#if WITH_EDITOR

	const FPreviewPlatformInfo info = GEditor->PreviewPlatform;
	const EShaderPlatform shaderPlatform = GetFeatureLevelShaderPlatform(info.GetEffectivePreviewFeatureLevel());
	const bool isMobile = IsMobilePlatform(shaderPlatform);

#elif (PLATFORM_IOS || PLATFORM_ANDROID)

	const bool isMobile = IsMobilePlatform(shaderPlatform);

#endif

```

### 苹果分辨率

https://blog.csdn.net/iOS1501101533/article/details/121434858

https://dev.epicgames.com/documentation/zh-cn/unreal-engine/setting-up-device-profiles-in-unreal-engine?application_version=5.5

https://dev.epicgames.com/documentation/en-us/unreal-engine/performance-guidelines-for-mobile-devices-in-unreal-engine

苹果存在 点分辨率 和 比例因子 和 像素分辨率     点分辨率 * 比例因子 = 像素分辨率

UE [[UIScreen mainScreen] bounds] 获取的是点分辨率

然后再乘以 比例因子 r.MobileContentScaleFactor  得到当前的苹果分辨率

比例因子 默认值是  2,  如果要原生分辨率在 iphone6+ 后 需要是3

不过其实写0 也是原生分辨率

### 苹果抓帧后不能debug shader

https://dev.epicgames.com/documentation/zh-cn/unreal-engine/debugging-ios-projects-with-xcode-in-unreal-engine

https://dev.epicgames.com/documentation/en-us/unreal-engine/debugging-the-shader-compile-process-in-unreal-engine

提示 需要 import metal source

>> if building with the 'metal' command line tool, add the options '-gline-tables-only' and '-MO' to your compilation step.

找到, 开启下面选项

Engine/Config/ConsoleVariables.ini

```
r.Shaders.Optimize=0

// UE 4.x
r.Shaders.KeepDebugInfo=1

// UE 5.x
r.Shaders.Symbols=1
r.Shaders.ExtraData=1
```

### 苹果内存不够闪退

https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.developer.kernel.extended-virtual-addressing

https://imzlp.com/posts/56381/

开启虚拟内存, Extended Virtual Addressing Entitlement

在XCode -> 项目设置 -> Signing & Capabilities -> + Capability(添加) -> Extented Virtual Addressing

### Shader内存过大

https://imzlp.com/posts/15810/

1. 关闭 Support low quality lightmap shader permutations
  + 这意味着引擎支持为低质量的光照贴图生成不同的着色器版本
2. 关闭 Support Combined Static and CSM Shadowing
  + 这表示引擎支持将静态阴影和Cascaded Shadow Maps(CSM)阴影合并
3. 关闭 Support PointLight WholeSceneShadows
  + 这个功能允许点光源投射的阴影覆盖整个场景, 而不仅仅是局部区域
4. 关闭 Support Stationary Skylight
  + 支持 固定位置旋转范围, 但是可以修改颜色和强度的 固定天光
5. 开启 Share Material Shader Code
  + 允许多个材质共享相同的着色器代码. 通过共享代码, 材质渲染过程中的一些计算可以复用
6. 开启 Shared Material Native Libraries
  + 共享材质着色器代码的本地库. 它允许不同的材质和材质实例使用同一份底层本地代码库

### Pix 因为开启 DLSS 无法正常截帧

启动参数添加 -ExecCmds="r.NGX.DLSS.Enable 0, r.Streamline.DLSSG.Enable 0"


### 慢放当前画面自由镜头指令

慢放画面 Slomo 0.0
自由镜头 ToggleDebugCamera 1


### Github Desktop 界面卡

Win11 开启 硬件加速导致的

https://github.com/desktop/desktop/issues/10488

打开 cmd.exe 运行 set GITHUB_DESKTOP_DISABLE_HARDWARE_ACCELERATION=1 , 再重启试一试

如果不行可能是因为Shell 导致的卡顿

File -> Options -> Integrations -> Shell 换成 Command Propmpt

### 控制台输出中文编码乱码

添加这行代码 system("chcp 65001");

C/C++ 文件编码格式改成 UTF-8 with bom 试一试


### 获取相机View Proj Matrix

因为 这个获取矩阵的 aspect 是 相机的aspect, 而不是屏幕的宽高比, 所以需要手动传入屏幕的宽高比.

```C++
CameraComp->bConstrainAspectRatio = true;


int32 ScreenWidth = GEngine->GameViewport->Viewport->GetSizeXY().X;
int32 ScreenHeight = GEngine->GameViewport->Viewport->GetSizeXY().Y;

CameraComp->SetAspectRatio(ScreenWidth / (float)ScreenHeight);

FMatrix ViewMatrix;
FMatrix ProjectionMatrix;
FMatrix ViewProjectionMatrix;
UGameplayStatics::CalculateViewProjectionMatricesFromViewTarget(this, ViewMatrix,
																ProjectionMatrix, ViewProjectionMatrix);

// MVP 
// (LocalToWorld * ViewProjectionMatrix)

```

### .gitignore 不生效

```
git rm -r --cached .
git add .
```

### 连连看UV被优化

```
float2 GetUV(FMaterialPixelParameters Parameters, bool useUV1)
{
	float2 uv = float2(0, 0);
#if NUM_TEX_COORD_INTERPOLATORS > 0
	#if NUM_TEX_COORD_INTERPOLATORS < 1
		uv = Parameters.TexCoords[0].xy;
	#else
		uv = Parameters.TexCoords[useUV1 ? 1 : 0].xy;
	#endif
#endif
	return uv;
}
```

因为用Custom Node 和 Shader/ush 写

连连看 认为不需要UV, UE会优化掉 VS Input/Output UV

解决办法 需要有UV输入, 可以不用



### HLSL 2021 新语法

https://devblogs.microsoft.com/directx/announcing-hlsl-2021/


### Metal Capture Frame Diabled / 不显示

https://developer.apple.com/documentation/xcode/capturing-a-metal-workload-in-xcode

Edit Scheme -> Run -> Options -> GPU Frame Capture -> Metal

选中 项目的xcodeproj -> Build Settings -> 搜索 Capture -> Metal Capture Enabled -> true

如果 Capture Frame 按钮还是灰色的 重启手机


## UE 性能分析

https://imzlp.com/posts/19135/

下面可以快速预览下内存
stat unit

GM 指令
+ stat memory #显示引擎中各个子系统的内存占用
+ stat MemoryAllocator #显示内存分配信息
+ stat MemoryPlatform #显示平台内存信息
+ stat MemoryStaticMesh #显示静态模型的内存信息

启动参数
+ -LLM #启用LLM
+ -LLMCSV #连续将所有值写入CSV文件, 自动启用-LLM
+ -llmtagsets=Assets #实验性功能, 显示每个资源分配的内存总计
+ -llmtagsets=AssetClasses #实验性功能, 显示每个UObject类类型的总计

开启LLM后, 运行下面GM
stat llm #显示LLM摘要, 所有较低级别的引擎统计信息都归入单个引擎统计信息。
stat llmfull #显示LLM所有统计信息
stat LLMPlatform #显示从OS分配的所有内存信息 
stat LLMOverhead #显示LLM内部使用的内存

要生成更详细的内存报告, 可以使用 MemReport 配合 -full 参数:

MemReport -full

生成的报告将保存在 Game/Saved/Profiling/MemReports 目录下，文件格式为 .memreport

Android 地址: \ > storage > emulated > 0 > Android > data > com.example.myapp > files > UnrealGame > myapp > myapp > saved > Profiling  > MemReports

或者直接用下面的bat

```bat
adb pull  /sdcard/Android/data/com.example.myapp/files/UnrealGame/myapp/myapp/Saved/Logs/. ./Logs/
adb pull  /sdcard/Android/data/com.example.myapp/files/UnrealGame/myapp/myapp/Saved/Profiling/. ./Profiling/
pause

```

通常只用看 ResExcKB 这个就好了, 可以用同文件夹下的 MemreportToCSV.py 转换为CSV

https://www.intel.cn/content/www/cn/zh/developer/articles/technical/unreal-engine-optimization-profiling-fundamentals.html

+ Count - instances of UObject
+ NumKB - the amount of memory used by the UObject
+ ResExcKB - the amount of memory used by resources owned by this UObject
+ ResExcDedSysKB - the amount of memory in system memory
+ ResExcDedVidKB - the amount of memory in dedicated video memory

ADB 查看内存

这个命令会输出系统中所有进程的内存信息, 包括 PSS/USS/RSS 等
adb shell dumpsys meminfo

输出某个 APP的 内存
adb shell dumpsys meminfo com.example.myapp

或者 先获取 PID 在 根据PID 输出 特定APP的内存
adb shell pidof com.example.myapp
adb shell dumpsys meminfo <pid>

## 查看运行时引用

GM指令输入, 可以查看引用关系


obj refs name=VT_PerlinWorley_Balanced

然后找到代码构造函数中的一些强制引用, 添加HasAnyFlags, 去掉加载

```C++
if (!HasAnyFlags(RF_ClassDefaultObject | RF_ArchetypeObject | RF_DefaultSubObject))
{
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> VolumetricCloudDefaultMaterialRef(TEXT("/Engine/EngineSky/VolumetricClouds/m_SimpleVolumetricCloud_Inst.m_SimpleVolumetricCloud_Inst"));
	Material = VolumetricCloudDefaultMaterialRef.Object;
}
```

## 只加载特定质量的shader

只加载特定质量的shader, 提高加载速度, 节省内存, 但是不方便切画质了

AndroidEngine.ini

```
[/Script/Engine.RendererSettings]
r.DiscardUnusedQuality=True
```


## 修改UE Shader Compile 速度

打开 UnrealEngine\Engine\Config\BaseEngine.ini

修改下面

```

PercentageUnusedShaderCompilingThreads=0
; 改成1会比较卡
WorkerProcessPriority=0

```

## Nanite 和 DDX/DDY

PC 开了 Nanite后 用硬件的DDX和DDY 会有 BUG, 速度会变慢很多, UE 自己算了一套DDX/DDY 在 5.7修复
比如在 CustomNode 里面 手动写 TextureSampleBias
https://issues.unrealengine.com/issue/UE-268303


## FXC saturate 精度编译报错

UE用FXC 做 mobile preview, saturate(half) 就会出现报错 需要强制转换为float


## 生成Patch

生成patch pak

```BAT
@ECHO OFF
set PakFilename="xxxx\Paks\pakchunk999-AndroidP.pak"
set ResponseFile="xxxx\ConfigPakList.txt"
set UnrealPak=".\Engine\Binaries\Win64\UnrealPak.exe"
CALL %UnrealPak% %PakFilename%  -create=%ResponseFile%
PAUSE
```

ConfigPakList.txt

```
xxxxxxx\Game\Config\Android\AndroidEngine.ini ../../../{appName}/Config/Android/
```

## 替换 exe debug

写一个 bat, 拷贝 xxxxx\Binaries\Win64 下的  appName.exe 和 appName.pdb 去替换

```BAT

set clientconfig=Development
set cookconfig=-SkipCook
set pakconfig=-SkipPak 

call XXXXXXX\Engine\Build\BatchFiles\RunUAT.bat BuildGame -project="XXXXXXX\FY.uproject" -nop4 -prereqs -clientconfig=%clientconfig% %cookconfig% -targetplatform=Win64 -utf8output 

```

## 关闭RHI异步

启动添加

-ExecCmds="r.RHIThread.Enable 0, r.RDG.ImmediateMode 1, r.RDG.Debug.FlushGPU 1"

## 遍历特定 Actor Class

```C++

for (TActorIterator<XXXXXXX> It(GetWorld()); It; ++It)
{
	XXXXXXX* actor = *It;
}

```

## 变体统计

打开编辑 Engine\Config\ConsoleVariables.ini

```
r.ShaderDevelopmentMode=1

r.DumpShaderDebugInfo=1
```

cook完后会在 {项目目录}\Saved\MaterialStats下生成变体统计文件
Cooked 是 最终变体Shader 的数量(建议参考这个), Permutations 是ShaderFeature的数量

{项目目录}\Saved\MaterialStatsDebug 是详细的变体枚举
PermutationString 是 ShaderFeature 排列

Cooked = 每个 Permutations 的 Uses 累加

怎么看 Uses 的详情? 随便举个例子, cook生成了2个变体目录, 每个 又有6个子文件夹

下面就是cook生成的中间结果, 2 (Permutations) * 6 (Uses) = 12 (Cooked)

{项目目录}\Saved\ShaderDebugInfo\VULKAN_ES3_1_ANDROID\M_Test_e6f739dfdb823b6d\Default\FLocalVertexFactory
{项目目录}\Saved\ShaderDebugInfo\VULKAN_ES3_1_ANDROID\M_Test_155e94de3daa0004\Default\FLocalVertexFactory

  + TMobileBasePassPSFMobileDirectionalLightAndCSMPolicyLOCAL_LIGHTS_DISABLED
  + TMobileBasePassPSFMobileDirectionalLightAndCSMPolicyLOCAL_LIGHTS_ENABLED
  + TMobileBasePassPSFNoLightMapPolicyLOCAL_LIGHTS_DISABLED
  + TMobileBasePassPSFNoLightMapPolicyLOCAL_LIGHTS_ENABLED
  + TMobileBasePassVSFMobileDirectionalLightAndCSMPolicy
  + TMobileBasePassVSFNoLightMapPolicy

## stat 相关指令

https://dev.epicgames.com/documentation/zh-cn/unreal-engine/stat-commands-in-unreal-engine

## 包体启用 Insights

如果是PC包 启动项添加

```Bat
-trace=cpu,frame,bookmark,log,loadtime,file,net,gpu,memory -statnamedevents -LLM -LLMCSV
```

如果是安卓包

PC执行

```bat
adb reverse tcp:1980 tcp:1980
adb shell setprop debug.ue.commandline -tracehost=127.0.0.1
pause
```

安卓启动项命令行添加

```bat
-forcevulkanddrawmarkers -ExecCmds="stat fps, stat unit" -trace=cpu,frame,bookmark,log,loadtime,file,net,gpu,memory -statnamedevents -LLM -LLMCSV
```

## debug d3d 命令

启动参数添加 -d3ddebug

## 用代码创建的Volume没有gizmos

代码创建的Volume没有, 但是点击拖进来的Volume 有

需要手动添加 CreateBrushForVolumeActor

```C++
UCubeBuilder* builder = NewObject<UCubeBuilder>();
UActorFactory::CreateBrushForVolumeActor(newActor, builder);

newActor->PostEditChange();
newActor->PostEditMove(true);

```
## FString 条件断点FString

```C++
wcsstr(*(const wchar_t**)((const char*)&MyString + 0), L"156") != 0
```

## 命令编译项目

命令编译项目, 用于代码打包编译检测通过

```Bat
:: Windows Editor
call {引擎地址}\Engine\Build\BatchFiles\Build.bat {AppName}Editor Win64 Development "{项目路径}\{AppName}.uproject"

:: Android
call {引擎地址}\Build.bat {AppName} Android Development ""{项目路径}\{AppName}.uproject"
```

## Device Output Log

可以看Log 和 输入指令

{引擎地址}\Engine\Binaries\Win64\UnrealFrontend.exe

## 增量Cook

打包Bat中添加

-AdditionalCookerOptions="-noshaderddc -iterative"

或

-iterativecooking


## AFS

Shipping 包有时候用 ADB 无法正常推送 或者 读取不到 uproject

AndroidFileServer是虚幻专为Android平台开发的一款文件服务系统。

Android SDK版本在30(Android 10)以上, 原有的UE4Game文件夹无法再创建到Android根目录

即使使用外部公共目录也无法直接通过手机获取到日志文件, 以及部分Save下的文件内容, ROOT的手机应该可以看到, 但引擎默认是固定死的这个路径的

如果不用AFS, 需要自己去修改源码把这些路径重定向到Android新版本支持的目录下, 而AFS则解决了上述问题


## 打开文件夹选中文件

```C++

void OpenSelectFile(FString path)
{
	if (FPaths::FileExists(path))
	{
		FString absolutePath = FPaths::ConvertRelativePathToFull(path);
		// 注意这里要用 '\' 而不是 '/'
		absolutePath = absolutePath.Replace(TEXT("/"),TEXT("\\"));

		FString arguments = FString::Printf(TEXT("/select,\"%s\""), *absolutePath);

		FPlatformProcess::CreateProc(TEXT("explorer.exe"), *arguments, true, false, false, nullptr, 0, nullptr, nullptr);
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("File does not exist: %s"), *path);
	}
}


```

## 多线程执行


```C++

#include "Async/ParallelFor.h"

FCriticalSection ResultCS;

ParallelFor(allTextures.Num(), [&](int32 Index)
{
	TObjectPtr<UTexture2D> item = allTextures[Index];
	FString texHash;
	const bool isValid = GetTextureHash(item, texHash);
	if (isValid)
	{
		FScopeLock Lock(&ResultCS);

		// Dothing...
	}
});

```

## Mobile Cluster Deferred Lighting

指令执行

r.Mobile.UseClusteredDeferredShading 1

如果出现乱闪, 可能是Per Cell Max Light 过小, 尝试下面这个

r.Forward.MaxCulledLightsPerCell 64

## Mobile Float 精度

"0: Use Half-precision (default)"
"1: Half precision, except Full precision for material expressions"
"2: Force use of high precision in pixel shaders."

r.Mobile.FloatPrecisionMode=1

## 关闭UDP

因为UDP 会有大量的网络占用, 启动参数添加

-UDPMESSAGING_TRANSPORT_ENABLE=0
