UWA其它
======

(Github正常排版: [UWA其它][0])

-----------------

因为知识点比较少, 要么都是以前说过的, 就索性合成一篇文章.

括号()内的话都是我自己想的.

-----------------

<!-- @import "[TOC]" {cmd="toc" depthFrom=1 depthTo=6 orderedList=false} -->

<!-- code_chunk_output -->

- [**1. Unity移动游戏性能优化案例分析**](#-1-unity移动游戏性能优化案例分析-)
  - [**1.1 URP**](#-11-urp-)
    - [**1.1.1 使用URP的项目占比?**](#-111-使用urp的项目占比-)
    - [**1.1.2 RenderPipelineManager.DoRenderLoop_Internal消耗**](#-112-renderpipelinemanagerdorenderloop_internal消耗-)
    - [**1.1.3 SRP Batcher会失效**](#-113-srp-batcher会失效-)
    - [**1.1.4 OverDraw**](#-114-overdraw-)
    - [**1.1.5 Renderer Feature**](#-115-renderer-feature-)
  - [**1.2 Custom Bloom**](#-12-custom-bloom-)
  - [**1.3 带宽**](#-13-带宽-)
  - [**1.4 Shader**](#-14-shader-)
  - [**1.5 Spine**](#-15-spine-)
  - [**1.6 TextMeshPro**](#-16-textmeshpro-)

<!-- /code_chunk_output -->

-----------------

## **1. Unity移动游戏性能优化案例分析**
  [视频地址][2]

### **1.1 URP**
  
#### **1.1.1 使用URP的项目占比?**
  + 2021 Q4 37%
  + 2022 Q1 42%
  + 2022 Q2 49%
  + 2022 Q3 54% 

#### **1.1.2 RenderPipelineManager.DoRenderLoop_Internal消耗**
  + 本身消耗
  + GPU压力影响
  + 相机数量影响

函数消耗没有特别集中的点.

![](Images/UWAOther_00.jpg)

![](Images/UWAOther_01.jpg)

![](Images/UWAOther_02.jpg)

GPU压力. 分辨率降低RenderLoop耗时明显降低.

|OPPO R17|2340x1080 (1.0)|1872x864 (0.8)|1170x540 (0.5)|
|-|-|-|-|
|Renderloop耗时均值(ms)|8.75|6.76|3.55|
|FPS|23.05|34.84|58.97|
|GfxWaitForPresent (ms)|17.49|9.29|4.84|

相机数量影响. 这里的相机什么都没有绘制, 但是还是存在一定的消耗, 所以关闭/减少无效的相机, 尽量合并相机.

|OPPO R17|1170x540(0个)|1170x540(1个)|1170x540(2个)|1170x540(3个)|
|-|-|-|-|-|
|Renderloop耗时均值(ms)|3.55|6.15|7.54|9.11|
|FPS|58.97|56.91|52.42|46.84|

#### **1.1.3 SRP Batcher会失效**

1. 特定的几个版本OpenGL下 SRP Batch会失效.

![](Images/UWAOther_03.jpg)

2. MaterialPropertyBlock(MPB)和SRP Batcher不兼容.

3. 多灯光对粒子系统合批的影响.

  不同粒子受到的灯光不同就会不能Batch. 

  因为特效经常不受灯光影响. 所以可以把粒子系统的Layer标记成FX, 灯光的Culling Mask取消勾选FX层.

  但是这种改法在不同版本中生效的情况不一样.

![](Images/UWAOther_04.jpg)

![](Images/UWAOther_05.jpg)

![](Images/UWAOther_06.jpg)

#### **1.1.4 OverDraw**

  原来的OverDraw方法会失效, 所以用了一套新的方案代替. [代码仓库][3]

  然后自己再写一个Compute Shader, 对全屏Over DrawRT做累加, 除以像素数量, 得到平均值.

![](Images/UWAOther_07.jpg)

![](Images/UWAOther_08.jpg)

#### **1.1.5 Renderer Feature**
  注意Renderer Feature在多个相机上会产生效果, 所以会产生无用的开销. 
  
  如果一些相机不要这些效果, 可以创建空的Renderer, 为相机指定Render.

  (其实也可以根据CameraName CameraTag来直接return.)

![](Images/UWAOther_09.jpg)

![](Images/UWAOther_10.jpg)

  还有比如说只有选中的时候才出现描边, 正常的情况下不用. 那么就可以做成动态开关.

  (他是通过反射去获取的. 其实也没有必要, 直接加一个static bool之类的都可以.)

![](Images/UWAOther_11.jpg)

```C#

public static class ScriptableRendererExtension
{
	private static readonly Dictionary<ScriptableRenderer, Dictionary<string, ScriptableRendererFeature>> s_renderFeatures = new Dictionary<ScriptableRenderer, Dictionary<string, ScriptableRendererFeature>>();

	public static ScriptableRendererFeature GetRendererFeature(this ScriptableRenderer renderer, string name)
	{
		if (!s_renderFeatures.TryGetValue(renderer, out var innerFeatures))
		{
			var propertyInfo = renderer.GetType().GetProperty("rendererFeatures", BindingFlags.Instance | BindingFlags.NonPublic);
			List<ScriptableRendererFeature> rendererFeatures = (List<ScriptableRendererFeature>)propertyInfo?.GetValue(renderer);
			if (rendererFeatures == null)
			{
				s_renderFeatures[renderer] = null;
			}
			else
			{
				innerFeatures = new Dictionary<string, ScriptableRendererFeature>();
				for (var i = 0; i < rendererFeatures.Count; i++)
				{
					var feature = rendererFeatures[i];
					innerFeatures[feature.name] = feature;
				}
				s_renderFeatures[renderer] = innerFeatures;
			}
		}
		if (innerFeatures != null)
		{
			innerFeatures.TryGetValue(name, out var result);
			return result;
		}
		return null;
	}
}

```

```C#

public void SwitchSSAO(bool active)
{
	var data = Camera.main.GetUniversalAdditionalCameraData();
	var feature = data.scriptableRenderer.GetRendererFeature("NewScreenSpaceAmbientOcclusion");
	feature.SetActive(active);
}

```

### **1.2 Custom Bloom**

  想要不同特效Bloom效果不一样. 其实就是利用MRT(Color RT + Mask RT)去绘制特效. 

  ![](Images/UWAOther_12.jpg)

  判断是否是MRT就是**RenderingUtils.IsMRT(renderPass.colorAttachments)**.

  然后就是C# 设置MRT, Shader那边修改SV_Target为MRT. C# 记得Clear RT Color.

  Mask记录当前特效自定义的Bloom的Threshold. 剔除过低Alpha的像素. Blend Mode记得改成MRT的.

  然后替换Bloom Shader中的threshold的值. 他这里Mask为1 则为volume的threshold.

  但是有个缺点, 因为需要修改MRode的Blend Mode, 所以需要OpenGLES 3.2. 比如说小米4X直接不渲染, 5XBlend Mode 没有修改成功, OPPO R17则修改成功.

```C#
internal static bool IsMRT(RTHandle[] colorBuffers)
{
	return GetValidColorBufferCount(colorBuffers) > 1;
}

internal static uint GetValidColorBufferCount(RTHandle[] colorBuffers)
{
	uint nonNullColorBuffers = 0;
	if (colorBuffers != null)
	{
		foreach (var identifier in colorBuffers)
		{
			if (identifier != null && identifier.nameID != 0)
				++nonNullColorBuffers;
		}
	}
	return nonNullColorBuffers;
}
```

![](Images/UWAOther_13.jpg)

![](Images/UWAOther_14.jpg)

![](Images/UWAOther_15.jpg)

![](Images/UWAOther_16.jpg)

![](Images/UWAOther_17.jpg)

### **1.3 带宽**

  Copy Depth Pass, 会增加很高的带宽. 因为会切换RT. 增加了一次RAM到RAM的拷贝. 使得所有的Tile多了一次Load和Store.

![](Images/UWAOther_18.jpg)

  改进就是使用FramebufferFetch. 比如说: GL_ARM_shader_framebuffer_fetch_depth_stencil.

下面是OpenGL Depth版本, 可能要把Unity的ShaderLab改成GLSL.

```C++
#ifdef FRAGMENT
#version 320 es
#extension GL_ARM_shader_framebuffer_fetch_depth_stencil : enable

#ifdef GL_EXT_shader_texture_lod
#extension GL_EXT_shader_texture_lod : enable
#endif

#endif
```

原本获取Depth是通过纹理采样的方式: float depth = texture(_CameraDepthTexture, uv.xy).x;

可以更改为: loat depth = gl_LastFragDepthARM:

Fetch Depth优化效果, 小米10S 90FPS 2340x1080

| |Copy Depth|Fetch Depth|
|-|-|-|
|Read|3.5G/s|2.9G/s|
|Write|1.1GMB/s|480MB/s|

下面是Unity的默认的inout color版本.

```C++
#include "UnityCG.cginc"
#pragma vertex vert
#pragma fragment frag
// in practice: only compile for gles2,gles3,metal
#pragma only_renderers framebufferfetch

struct appdata_t {
	float4 vertex : POSITION;
	float2 texcoord : TEXCOORD0;
};

struct v2f {
	float4 vertex : SV_POSITION;
	fixed4 color : TEXCOORD0;
};

v2f vert (appdata_t v)
{
	v2f o;
	o.vertex = mul(UNITY_MATRIX_MVP, v.vertex);
	o.color.rg = v.texcoord*4.0;
	o.color.ba = 0;
	return o;
}

void frag (v2f i, inout fixed4 ocol : SV_Target)
{
	i.color = frac(i.color);
	ocol.rg = i.color.rg;
	ocol.b *= 1.5;
}
```

兼容问题?

低端机不太行. Mali的layout的顺序必须从0开始, 然后严格连续. 高通则没事.

![](Images/UWAOther_19.png)

![](Images/UWAOther_20.jpg)

![](Images/UWAOther_21.png)

### **1.4 Shader**

精度: 手机端合理使用float/half, 减少Shader复杂度.

条件分支: 手动指定UNITY_BRANCH, UNITY_FLATTEN.

UNITY_BRANCH: GPU会先执行if表达式里的条件,若条件返回true, 则后续仅执行true对应的那一段代码. 但会打乱执行顺序, 不适合并行处理.

UNITY_FLATTEN: GPU会执行所有分支的代码，在后面才通过if表达式里的条件来选取其中一个分支的结果. 更适合于并行处理.

如果什么都不标记的话编译器会按自己的判断选择其中之一, 然而不是每个平台每个版本的编译器都足够聪明, 开发中最好可以进行手动指定.

比如说下面代码如果没有指定UNITY_BRANCH, 则会计算条件里面的代码, 然后最后的阶段用bool值来做取舍.

如果添加了, 则会先判断if.

![](Images/UWAOther_22.jpg)

![](Images/UWAOther_23.jpg)

![](Images/UWAOther_24.jpg)

当if判断为true执行的代码段增加的Shader复杂度较高时, 且本身判断结果对于所有像素来说是一致的 (例如Uniform变量作为判断条件的参数), 建议手动添加UNITY_BRANCH.

当if判断为true执行的代码段增加的Shader复杂度较低时, 可以考虑使用UNITY_FLATTEN, 从而减少if打断并行执行的状态.

### **1.5 Spine**

  动画单独拆分, 按需加载.

  (不要一个Anim Ctrl巨大无比, 比如展示界面的角色可能就唱跳Rapper, 但是你把不需要的跳舞等也放进来了. 根据不同情景合适拆分.)

### **1.6 TextMeshPro**

1. 动态图集纹理被默认开启Read/Write Enabled改成静态图集, Generation Settins->Atlas Population Mode从Dynamic修改Static, 32MB->16MB. 如果规划好规划好字符集直接打静态.

如果有用户输入窗口生僻字怎么办? 使用一张512*512的动态图集作为上述静态图集的Fallback内存占用仅0.5MB，即总共16MB+0.5MB

2. 打出来的静态图集如果能完全包括所有可能的字符, 则解除引用(就是把Generation Settins->Source Font File 为空). 可以把字体文件的内存占用也节省下来 (有显示··的风险).

3. 图集纹理格式默认为Alpha8改成ASTC8x8, 16MB->4MB, Inspector中没有办法直接改.

先复制图集纹理到同一路径下, 设置压缩格式. 再替换TMP引用的图集纹理.

-----------------

-----------------

[1]:https://github.com/HHHHHHHHHHHHHHHHHHHHHCS/MyStudyNote/blob/main/MyUWA2022Note/%E7%A7%BB%E5%8A%A8%E7%AB%AF%E5%AE%9E%E6%97%B6GI%E6%96%B9%E6%A1%88.md
[2]:https://edu.uwa4d.com/course-intro/1/486?entrance=3
[3]:https://github.com/ina-amagami/OverdrawForURP