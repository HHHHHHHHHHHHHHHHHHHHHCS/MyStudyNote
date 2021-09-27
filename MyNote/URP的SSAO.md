URP的SSAO
=================

(Github正常排版: [URP的SSAO]())

-----------------

## **0.先放结论**

&emsp;&emsp; URP去年更新了SSAO,很久之前写(抄)完一直没有写个文章记录学习下.最近放假就写一下.

食()用方法很简单.打开**RenderData**, 再**Add Renderer Feature**, 选择**Screen Space Ambient Occlusion**就好了.

![URPSSAO_0](Images/URPSSAO_0.jpg)

然后看下对比效果.现在是没有开.

![URPSSAO_1](Images/URPSSAO_1.png)

我想开了.

![URPSSAO_2](Images/URPSSAO_2.png)

再看下耗时.虽然用render doc来检测耗时不是很科学和准确,但是手里也没有别的工具了.

![URPSSAO_3](Images/URPSSAO_3.png)

![URPSSAO_4](Images/URPSSAO_4.png)

![URPSSAO_5](Images/URPSSAO_5.png)

差不多5ms.这效果配上这耗时真的一言难尽...... 但是不妨碍拿来学习.

这里的版本是2021的. 2021对延迟渲染和XR做了支持,并且可以修改渲染的时机为BeforeOpaque/AfterOpaque(就是在物体shader中采样,还是贴到屏幕上).

下图是2020版的设置. 可以和上面对比一下, 基本没有什么大改动.

![URPSSAO_6](Images/URPSSAO_6.jpg)


-----------------

## **1.拆解C#**

&emsp;&emsp; 我的习惯是先拆解C#,再学习shader. 我这里是自己复制改动了一些,方便自己区分.可以对照源码看.

先拆解设置属性,看看都有啥. 看上面属性面板很简单, 看了一眼代码果然很简单呢.

```C#
[Serializable]
public class URPSSAOSettings
{
	// Enums
	public enum DepthSource
	{
		Depth = 0,
		DepthNormals = 1,
	}

	public enum NormalQuality
	{
		Low,
		Medium,
		High
	}

	// Parameters
	[SerializeField] public bool Downsample = false;
	[SerializeField] public bool AfterOpaque = false;
	[SerializeField] public DepthSource Source = DepthSource.DepthNormals;
	[SerializeField] public NormalQuality NormalSamples = NormalQuality.Medium;
	[SerializeField] public float Intensity = 3.0f;
	[SerializeField] public float DirectLightingStrength = 0.25f;
	[SerializeField] public float Radius = 0.035f;
	[SerializeField] public int SampleCount = 4;
}
```

然后再看**RendererFeature**. 这个里面基本就是创建个渲染Pass,是否添加到渲染队列,创建材质和存个设置. 
**[DisallowMultipleRendererFeature]**这个标签作用是禁止多次添加用的,在2020是**internal**加上去会报错,2021是**public**.
**Dispose**在切换**RendererData**的时候会触发,销毁创建的材质.

```C#
using System;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

[DisallowMultipleRendererFeature]
[Tooltip("The Ambient Occlusion effect darkens creases, holes, intersections and surfaces that are close to each other.")]
public class URPSSAORenderFeature : ScriptableRendererFeature
{
	// Constants
	private const string k_ShaderName = "Hidden/Universal Render Pipeline/ScreenSpaceAmbientOcclusion";

	// Serialized Fields
	[SerializeField, HideInInspector] private Shader m_Shader = null;
	[SerializeField] private URPSSAOSettings m_Settings = new URPSSAOSettings();

	// Private Fields
	private Material m_Material;
	private URPSSAORenderPass m_SSAOPass = null;

	/// <inheritdoc/>
	public override void Create()
	{
		// Create the pass...
		if (m_SSAOPass == null)
		{
			m_SSAOPass = new URPSSAORenderPass();
		}

		GetMaterial();
	}

	/// <inheritdoc/>
	public override void AddRenderPasses(ScriptableRenderer renderer, ref RenderingData renderingData)
	{
		if (!GetMaterial())
		{
			Debug.LogErrorFormat(
				"{0}.AddRenderPasses(): Missing material. {1} render pass will not be added. Check for missing reference in the renderer resources.",
				GetType().Name, m_SSAOPass.profilerTag);
			return;
		}

		bool shouldAdd = m_SSAOPass.Setup(m_Settings, renderer, m_Material);
		if (shouldAdd)
		{
			renderer.EnqueuePass(m_SSAOPass);
		}
	}

	/// <inheritdoc/>
	protected override void Dispose(bool disposing)
	{
		CoreUtils.Destroy(m_Material);
	}

	private bool GetMaterial()
	{
		if (m_Material != null)
		{
			return true;
		}

		if (m_Shader == null)
		{
			m_Shader = Shader.Find(k_ShaderName);
			if (m_Shader == null)
			{
				return false;
			}
		}

		m_Material = CoreUtils.CreateEngineMaterial(m_Shader);
		return m_Material != null;
	}
}

```

然后就再看**RenderPass**.
这里先看构造函数
因为我这里是抄写的,比较符合我自己的代码习惯,而且还是一步一步慢慢填充的,所以跟原来的代码不一样.但是大体上的思想基本一致.
比如说**ProfilingSampler.Get(URPProfileId.SSAO)**外部获取不了,我这里用**k_tag**来自己创建.
再比如**isRendererDeferred**判断是否为延迟渲染.因为 **renderer.renderingMode** 是internal, 所以没有办法判断, 只能先写成false. 后面再在settings里面加个bool(后面再写).

```C#
using System;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

public class URPSSAORenderPass : ScriptableRenderPass
{
	private const string k_tag = "URPSSAO";

	// Private Variables
	// private ProfilingSampler m_ProfilingSampler = ProfilingSampler.Get(URPProfileId.SSAO);
	private URPSSAOSettings m_CurrentSettings;

	// Properties
	private bool isRendererDeferred =>
			false; //m_Renderer is UniversalRenderer renderer && renderer.renderingMode == RenderingMode.Deferred;

	internal URPSSAORenderPass()
	{
		profilingSampler = new ProfilingSampler(k_tag);
		m_CurrentSettings = new URPSSAOSettings();
	}

	public override void Execute(ScriptableRenderContext context, ref RenderingData renderingData)
	{
		throw new System.NotImplementedException();
	}
}

```

然后再看看每帧执行的**Setup**.
把**Feature**的属性传递进去.
根据属性决定是否要开启SSAO,渲染队列,和需要的场景信息.
(URP2021**ConfigureInput**终于支持**Motion Vector**)

```C#

internal URPSSAORenderPass()
{
	...
}

internal bool Setup(URPSSAOSettings featureSettings, ScriptableRenderer renderer,
			Material material)
{
	m_Material = material;
	m_Renderer = renderer;
	m_CurrentSettings = featureSettings;

	URPSSAOSettings.DepthSource source;
	if (isRendererDeferred)
	{
		renderPassEvent = featureSettings.AfterOpaque
			? RenderPassEvent.AfterRenderingOpaques
			: RenderPassEvent.AfterRenderingGbuffer;
		source = URPSSAOSettings.DepthSource.DepthNormals;
	}
	else
	{
		// Rendering after PrePasses is usually correct except when depth priming is in play:
		// then we rely on a depth resolve taking place after the PrePasses in order to have it ready for SSAO.
		// Hence we set the event to RenderPassEvent.AfterRenderingPrePasses + 1 at the earliest.
		renderPassEvent = featureSettings.AfterOpaque
			? RenderPassEvent.AfterRenderingOpaques
			: RenderPassEvent.AfterRenderingPrePasses + 1;
		source = m_CurrentSettings.Source;
	}


	switch (source)
	{
		case URPSSAOSettings.DepthSource.Depth:
			ConfigureInput(ScriptableRenderPassInput.Depth);
			break;
		case URPSSAOSettings.DepthSource.DepthNormals:
			// need depthNormal prepass for forward-only geometry
			ConfigureInput(ScriptableRenderPassInput.Normal);
			break;
		default:
			throw new ArgumentOutOfRangeException();
	}

	return m_Material != null
			&& m_CurrentSettings.Intensity > 0.0f
			&& m_CurrentSettings.Radius > 0.0f
			&& m_CurrentSettings.SampleCount > 0;
}

```

当成功加入到渲染队列之后,就是**OnCameraSetup**.
(这里只是按照用到的方法顺序说明,比如**Configure**,**FrameCleanup**都是空方法就跳过顺序说明了.)
这里主要是对材质球的属性设置.所以需要属性ID.粘贴一下,啪很快啊.
 
 
