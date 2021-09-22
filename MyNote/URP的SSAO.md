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

&emsp;&emsp; 我的习惯是先拆解C#,再学习shader. 我这里是自己复制改动了一些,可以对照源码看.

先拆解设置属性,看看都有啥. 看上面属性面板很简单, 看了一眼代码果然很简单呢.

```C#
[Serializable]
public class ScreenSpaceAmbientOcclusionSettings
{
	// Enums
	public enum DepthSource
	{
		Depth = 0,
		DepthNormals = 1,
		//GBuffer = 2
	}

	public enum NormalQuality
	{
		Low,
		Medium,
		High
	}

	// Parameters
	[SerializeField] public bool Downsample = false;
	[SerializeField] public DepthSource Source = DepthSource.DepthNormals;
	[SerializeField] public NormalQuality NormalSamples = NormalQuality.Medium;
	[SerializeField] public float Intensity = 3.0f;
	[SerializeField] public float DirectLightingStrength = 0.25f;
	[SerializeField] public float Radius = 0.035f;
	[SerializeField] public int SampleCount = 6;
}
```

然后再看**RendererFeature**. 这个里面基本就是创建个渲染Pass,创建材质和存个设置. 
因为[DisallowMultipleRendererFeature]是**internal**修饰符(坏文明),作用是禁止多次添加用的,要去掉不然会报错.

```C#
//[DisallowMultipleRendererFeature]
public class ScreenSpaceAmbientOcclusion : ScriptableRendererFeature
{
	private const string k_ShaderName = "Hidden/Universal Render Pipeline/ScreenSpaceAmbientOcclusion";

	// Serialized Fields
	[SerializeField, HideInInspector] private Shader m_Shader = null;
	[SerializeField] private ScreenSpaceAmbientOcclusionSettings m_Settings = new ScreenSpaceAmbientOcclusionSettings();

	// Private Fields
	private Material m_Material;
	private ScreenSpaceAmbientOcclusionPass m_SSAOPass = null;

	/// <inheritdoc/>
	public override void Create()
	{
		// Create the pass...
		if (m_SSAOPass == null)
		{
			m_SSAOPass = new ScreenSpaceAmbientOcclusionPass();
		}

		GetMaterial();
		m_SSAOPass.profilerTag = name;
		m_SSAOPass.renderPassEvent = RenderPassEvent.BeforeRenderingOpaques;
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

		bool shouldAdd = m_SSAOPass.Setup(m_Settings);
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
		m_SSAOPass.material = m_Material;
		return m_Material != null;
	}
}

```