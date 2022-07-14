写写简单的HBAO
======

(Github正常排版: [写写简单的HBAO][1])

-----------------

<!-- @import "[TOC]" {cmd="toc" depthFrom=1 depthTo=6 orderedList=false} -->

<!-- code_chunk_output -->

- [**0. 起因**](#0-起因)
- [**1. 原理**](#1-原理)
- [**2. C#**](#2-c)
  - [**2.1 RenderSettings**](#21-rendersettings)
  - [**2.2 RenderFeature**](#22-renderfeature)
  - [**2.3 RenderPass**](#23-renderpass)
- [**3. Shader**](#3-shader)
  - [**3.1 基础的框架**](#31-基础的框架)
  - [**3.2 数据准备**](#32-数据准备)

<!-- /code_chunk_output -->

-----------------

## **0. 起因**

&emsp;&emsp; URP有SSAO, HDRP有GTAO. 所以摆烂学一个HBAO.

下面是效果图.

![](Images/HBAO_00.jpg)

![](Images/HBAO_01.jpg)

下面是URP的SSAO. 可以发现HBAO会软很多, 慢慢淡出.

![](Images/HBAO_08.jpg)

下面是自己洗的GTAO, 调参没有调对. GTAO多了多次弹射的结果, 感觉更黑了.

![](Images/HBAO_09.jpg)

下面随便写的RayTracingAO, 也没有仔细的调参. 但是基本的视觉效果是有了.

![](Images/HBAO_10.jpg)

自己调参可能有点不准确, 这是官方给的对比图.

![](Images/HBAO_02.jpg)


HBAO对比SSAO采样次数更少, 效果也好很多. 虽然可以用TSSAO来减少采样和降低噪点.

-----------------

## **1. 原理**

&emsp;&emsp; HBAO, Image-Space Horizon-Based Ambient Occlusion, 水平基准环境光遮蔽, 是一项英伟达于2008年提出的SSAO衍生版, 效果比SSAO更好. [文章地址][2]

YiQiuuu的有篇文章是关于HBAO原理和实现, 讲的详细且不错, [文章地址][3]. 这里直接快速引用概括一下.

1. 屏幕上的每一个像素, 做一个四等分的四条射线, 然后随机旋转一下. 每一个像素的随机角度不能一样, 否则效果很怪/是错的. 这里的四等分也可以是六等分, 八等分...

![](Images/HBAO_03.jpg)

2. 对于任意一条射线, 沿着射线方向生成一个一维的高度. 然后根据深度做RayMarch找到一个最大的水平角(Horizon Angle).

![](Images/HBAO_04.jpg)

3. 根据点P和它的法线(面法线), 计算它的切面角(Tangent Angle).

![](Images/HBAO_05.jpg)

4. 根据Horizon Angle和Tangent Angle, 得到AO. AO = sin(h) - sin(t).

至于为什么AO=角度差值? 

我的理解(个人理解)是 周围的东西对比当前点越高, 则表示光被周围东西遮挡的越多, 则越暗.

![](Images/HBAO_06.jpg)

为什么用面法线, 而不是顶点插值法线?

![](Images/HBAO_07.jpg)

看官网的PPT是说 如果用顶点插值法线去计算会得到错误的遮挡.

如果我们用的是顶点插值法线, 当P在拐弯位置的时候, 顶点插值法线和面法线不一致. 计算的半球起始位置就可能会是错的.

而根据View Space 利用ddx/ddy重新生成的法线是对的. 之前的SSAO篇中有介绍怎么重新生成法线.

但是我下面的代码还是会用NormalRT, 首先为了提高性能. 

下面是我用ddx/ddy重新生成的法线出的效果. 发现会出现奇怪的死黑的边缘和锯齿.

![](Images/HBAO_11.jpg)

如果用的是比较复杂算法生成NormalRT, 看着效果和Gbuffer的NormalRT产生的效果也差不多.

![](Images/HBAO_12.jpg)

而且物体一般都有NormalMap, 用深度图和算法重新生成的NormalRT是没有NormalMap的. 比如地表的石子用的是NormalMap, 就会出现下面的效果.

![](Images/HBAO_13.jpg)

![](Images/HBAO_14.jpg)

因此我这里还是用的GBuffer的Normal 或者 DepthNormals Pass 生成的NormalRT.

其实正确的应该是用BentNormalRT. BentNormal大体指光线大概率通过的平均方向/不被其他物体遮挡的方向. 因此生成这个也更麻烦, 业界做法常常是单个物体离线计算好的贴图.

![](Images/HBAO_15.jpg)

-----------------

## **2. C#**

&emsp;&emsp; 个人习惯, 先写C#吧.

### **2.1 RenderSettings**

创建一个C#文件**HBAORenderFeature.cs**. 先写RenderSettings.

```C#

using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

[System.Serializable]
public class HBAORenderSettings
{
	[Range(0.0f, 1.0f)] public float intensity = 1.0f;
	[Range(0.25f, 5.0f)] public float radius = 1.2f;
	[Range(16f, 256f)] public float maxRadiusPixels = 256;
	[Range(0.0f, 0.5f)] public float angleBias = 0.05f;
	[Min(0)] public float maxDistance = 150.0f;
	[Min(0)] public float distanceFalloff = 50.0f;
	[Range(0.0f,16.0f)] public float sharpness = 8.0f;
}


```

intensity: AO强度

radius: 射线半径

maxRadiusPixels: 最大半径的像素数量

angleBias: 角度阈值

maxDistance: AO的最大距离, 超过这个距离就没有AO了

distanceFalloff: AO的距离衰减, 淡出用

sharpness: 模糊深度权重

### **2.2 RenderFeature**

然后继续在C#文件**HBAORenderFeature.cs**中, 写RenderFeature. **HBAORenderPass** 在后面补充.

因为URP的生命周期越来越神奇 存在反复调用, 所以我用 **OnCreate()** 和 flag 来管理.

这里只是demo, **renderPassEvent**我是随便写的. 比如这里是**RenderPassEvent.BeforeRenderingPostProcessing**.

```C#

using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

[System.Serializable]
public class HBAORenderSettings
{
	...
}

public class HBAORenderFeature : ScriptableRendererFeature
{
	public Shader effectShader;
	public HBAORenderSettings renderSettings;

	private bool needCreate;
	private HBAORenderPass renderPass;
	private Material effectMat;

	public override void Create()
	{
		needCreate = true;
	}

	protected override void Dispose(bool disposing)
	{
		CoreUtils.Destroy(effectMat);
		if (renderPass != null)
		{
			renderPass.OnDestroy();
			renderPass = null;
		}
	}

	public void OnCreate()
	{
		if (!needCreate)
		{
			return;
		}

		needCreate = false;

		if (renderPass == null)
		{
			renderPass = new HBAORenderPass()
			{
				renderPassEvent = RenderPassEvent.BeforeRenderingPostProcessing,
			};
		}

		if (effectMat == null || effectMat.shader != effectShader)
		{
			CoreUtils.Destroy(effectMat);
			if (effectShader != null)
			{
				effectMat = CoreUtils.CreateEngineMaterial(effectShader);
			}
		}

		renderPass.OnInit(effectMat, renderSettings);
	}

	public override void AddRenderPasses(ScriptableRenderer renderer, ref RenderingData renderingData)
	{
		if (effectShader == null)
		{
			return;
		}

		OnCreate();
		renderer.EnqueuePass(renderPass);
	}
}

```

到这里RenderFeature基本就写完了.

### **2.3 RenderPass**

创建**HBAORenderPass.cs**文件. 先写一个基础框架.

```C#

using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

public class HBAORenderPass : ScriptableRenderPass
{
	private const string k_tag = "HBAO";

	private HBAORenderSettings settings;
	private Material effectMat;

	public HBAORenderPass()
	{
		profilingSampler = new ProfilingSampler(k_tag);
	}

	public void OnInit(Material _effectMat, HBAORenderSettings _renderSettings)
	{
		effectMat = _effectMat;
		settings = _renderSettings;
	}

	public void OnDestroy()
	{
	}

	public override void Configure(CommandBuffer cmd, RenderTextureDescriptor cameraTextureDescriptor)
	{
	}

	public override void Execute(ScriptableRenderContext context, ref RenderingData renderingData)
	{
		var cmd = CommandBufferPool.Get();
		using (new ProfilingScope(cmd, profilingSampler))
		{
			
		}

		context.ExecuteCommandBuffer(cmd);
		CommandBufferPool.Release(cmd);
	}
}

```

从前面知道我们需要depthRT和normalRT, 所以在**Configure**中配置ConfigureInput.

```C#

public class HBAORenderPass : ScriptableRenderPass
{
	...

	public override void Configure(CommandBuffer cmd, RenderTextureDescriptor cameraTextureDescriptor)
	{
		ConfigureInput(ScriptableRenderPassInput.Depth | ScriptableRenderPassInput.Normal);

	}

	...
}

```

然后我们需要一个随机旋和射线长度的噪音图, 这里我偷懒用了**ComputeBuffer**. 但是建议离线把Texture保存下来传入.

noise.x: 随机初始角度

noise.y: 射线随机初始化长度

```C#

public class HBAORenderPass : ScriptableRenderPass
{
	...

	private ComputeBuffer noiseCB;
	private HBAORenderSettings settings;
	private Material effectMat;

	...

	public void OnInit(Material _effectMat, HBAORenderSettings _renderSettings)
	{
		effectMat = _effectMat;
		settings = _renderSettings;
		if (noiseCB != null)
		{
			noiseCB.Release();
		}
		Vector2[] noiseData = GenerateNoise();
		noiseCB = new ComputeBuffer(noiseData.Length, sizeof(float) * 2);
		noiseCB.SetData(noiseData);
	}

	public void OnDestroy()
	{
		if (noiseCB != null)
		{
			noiseCB.Release();
			noiseCB = null;
		}
	}

	...

	public override void Execute(ScriptableRenderContext context, ref RenderingData renderingData)
	{
		...
	}

	private Vector2[] GenerateNoise()
	{
		Vector2[] noises = new Vector2[4 * 4];

		for (int i = 0; i < noises.Length; i++)
		{
			float x = Random.value;
			float y = Random.value;
			noises[i] = new Vector2(x, y);
		}

		return noises;
	}
}

```

然后就是Shader属性ID. 这里直接全部一把梭写完了, 方便不用来回折腾也可以自动补全.

```C#

public class HBARenderPass : ScriptableRenderPass
{
	private const string k_tag = "HBAO";

	private static readonly int hbaoRT_ID = Shader.PropertyToID("_HBAORT");
	private static readonly int hbaoBlurRT_ID = Shader.PropertyToID("_HBAOBlurRT");
	private static readonly int noiseCB_ID = Shader.PropertyToID("_NoiseCB");
	private static readonly int aoTex_ID = Shader.PropertyToID("_AOTex");
	private static readonly int intensity_ID = Shader.PropertyToID("_Intensity");
	private static readonly int radius_ID = Shader.PropertyToID("_Radius");
	private static readonly int negInvRadius2_ID = Shader.PropertyToID("_NegInvRadius2");
	private static readonly int maxRadiusPixels_ID = Shader.PropertyToID("_MaxRadiusPixels");
	private static readonly int angleBias_ID = Shader.PropertyToID("_AngleBias");
	private static readonly int aoMultiplier_ID = Shader.PropertyToID("_AOMultiplier");
	private static readonly int maxDistance_ID = Shader.PropertyToID("_MaxDistance");
	private static readonly int distanceFalloff_ID = Shader.PropertyToID("_DistanceFalloff");
	private static readonly int sharpness_ID = Shader.PropertyToID("_Sharpness");
	private static readonly int blurDeltaUV_ID = Shader.PropertyToID("_BlurDeltaUV");

	...

}

```

在 **Execute(ScriptableRenderContext context, ref RenderingData renderingData)** 方法中, 把Settings参数和NoiseCB等传输给GPU.

radius, 跟屏幕尺寸比例有关.

maxRadiusPixels, 跟屏幕分辨率有关.

```C#

public override void Execute(ScriptableRenderContext context, ref RenderingData renderingData)
{
	var cmd = CommandBufferPool.Get();
	using (new ProfilingScope(cmd, profilingSampler))
	{
		int width = renderingData.cameraData.cameraTargetDescriptor.width;
		int height = renderingData.cameraData.cameraTargetDescriptor.height;
		float fov = renderingData.cameraData.camera.fieldOfView;
		float tanHalfFovY = Mathf.Tan(0.5f * fov * Mathf.Deg2Rad);

		cmd.SetGlobalBuffer(noiseCB_ID, noiseCB);
		cmd.SetGlobalFloat(intensity_ID, settings.intensity);
		cmd.SetGlobalFloat(radius_ID, settings.radius * 0.5f * height / (2.0f * tanHalfFovY));
		cmd.SetGlobalFloat(negInvRadius2_ID, -1.0f / (settings.radius * settings.radius));
		float maxRadiusPixels = settings.maxRadiusPixels * Mathf.Sqrt((width * height) / (1080.0f * 1920.0f));
		cmd.SetGlobalFloat(maxRadiusPixels_ID, Mathf.Max(16, maxRadiusPixels));
		cmd.SetGlobalFloat(angleBias_ID, settings.angleBias);
		cmd.SetGlobalFloat(aoMultiplier_ID, 2.0f * (1.0f / (1.0f - settings.angleBias)));
		cmd.SetGlobalFloat(maxDistance_ID, settings.maxDistance);
		cmd.SetGlobalFloat(distanceFalloff_ID, settings.distanceFalloff);
	}

	context.ExecuteCommandBuffer(cmd);
	CommandBufferPool.Release(cmd);
}

```

然后就是申请RT, SetRT, 绘制HBAO, 别忘了释放RT.

Blur的模块之后再补充.

```C#

public override void Execute(ScriptableRenderContext context, ref RenderingData renderingData)
{
	...
	using (new ProfilingScope(cmd, profilingSampler))
	{
		...
		cmd.SetGlobalFloat(distanceFalloff_ID, settings.distanceFalloff);
	
		cmd.GetTemporaryRT(hbaoRT_ID, width, height, 0, FilterMode.Bilinear, RenderTextureFormat.R8, RenderTextureReadWrite.Linear);

		cmd.SetRenderTarget(hbaoRT_ID);
		CoreUtils.DrawFullScreen(cmd, effectMat, null, 0);

		cmd.ReleaseTemporaryRT(hbaoRT_ID);
	}
	...
}

```

这样简单的HBAO C#基本写完了.

-----------------

## **3. Shader**

### **3.1 基础的框架**

创建一个Shader文件 **HBAO.shader**. 写个空的框架进去.

```C++

Shader "HBAO"
{
	SubShader
	{
		Tags
		{
			"RenderType"="Opaque"
		}
		LOD 100

		Cull Off
		ZWrite Off
		ZTest Always

		Pass
		{

			Name "HBAO"

			HLSLPROGRAM
			#pragma vertex vert
			#pragma fragment frag

			#include "Packages/com.unity.render-pipelines.core/ShaderLibrary/Common.hlsl"
			#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

			struct a2v
			{
				uint vertexID :SV_VertexID;
			};

			struct v2f
			{
				float4 pos:SV_Position;
				float2 uv:TEXCOORD0;
			};


			v2f vert(a2v IN)
			{
				v2f o;
				o.pos = GetFullScreenTriangleVertexPosition(IN.vertexID);
				o.uv = GetFullScreenTriangleTexCoord(IN.vertexID);
				return o;
			}

			half frag(v2f IN) : SV_Target
			{
				float2 uv = IN.uv;

				return 1;
			}
			ENDHLSL
		}

	}
}

```

把C#的传入的参数写上. 

还有我们需要DephtRT和NormalRT, 把它们的include也写上, **DeclareDepthTexture.hlsl** 和 **DeclareNormalsTexture.hlsl**.

同时定义方向等分个数(DIRECTIONS)和射线步进次数(STEPS). 这里直接大力出奇迹! 8等分, 6步进.

我这里偷懒用了Buffer!!!

```C++

Pass
{

	Name "HBAO"

	HLSLPROGRAM

	...
	#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
	#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareDepthTexture.hlsl"
	#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareNormalsTexture.hlsl"

	...

	struct v2f
	{
		...
	};

	#define DIRECTIONS 8
	#define STEPS 6

	StructuredBuffer<float2> _NoiseCB;

	float _Intensity;
	float _Radius;
	float _NegInvRadius2;
	float _MaxRadiusPixels;
	float _AngleBias;
	float _AOMultiplier;
	float _MaxDistance;
	float _DistanceFalloff;

	v2f vert(a2v IN)
	{
		...
	}

	...

}

```

### **3.2 数据准备**

在循环判断HBAO之前还要在Fragment中做点数据准备.

-----------------

Settings

C#

Shader

Blur

-----------------

Low-Tessellation问题
bias

不连续问题
衰减

噪声
blur


-----------------

[1]:https://github.com/HHHHHHHHHHHHHHHHHHHHHCS/MyStudyNote/blob/main/MyNote/%E5%86%99%E5%86%99%E7%AE%80%E5%8D%95%E7%9A%84HBAO.md
[2]:https://developer.download.nvidia.cn/presentations/2008/SIGGRAPH/HBAO_SIG08b.pdf
[3]:https://zhuanlan.zhihu.com/p/103683536


https://blog.csdn.net/qjh5606/article/details/120001743

https://www.csdn.net/tags/MtTaAg2sOTIzOTM4LWJsb2cO0O0O.html

https://zhuanlan.zhihu.com/p/367793439