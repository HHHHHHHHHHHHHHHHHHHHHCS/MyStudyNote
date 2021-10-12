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

## **1.原理**
TODO:

-----------------

## **2.拆解C#**

&emsp;&emsp; 我的习惯是先拆解C#,再学习shader. 我这里是自己复制改动了一些,方便自己区分.可以对照源码看.

### **2.1 URPSSAOSettings**

先拆解设置属性,看看都有啥. 看上面属性面板很简单, 看了一眼代码果然很简单呢. 所以这里创建C# **URPSSAORenderFeature.cs**. 直接复制Settings Class.

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

public class URPSSAORenderFeature: MonoBehaviour
{
	...
}

```

### **2.2 URPSSAORenderFeature**

然后再看**RendererFeature**. 这个里面基本就是创建个渲染Pass,是否添加到渲染队列,创建材质和存个设置. 
**[DisallowMultipleRendererFeature]**这个标签作用是禁止多次添加用的,在2020是**internal**加上去会报错,2021是**public**.
**Dispose**在切换**RendererData**的时候会触发,销毁创建的材质.
**URPSSAORenderPass**在后面补充.
修改完善**class URPSSAORenderFeature**.
**k_ShaderName**要和Shader中的name对应, 并且打包的时候注意别剔除了(可以添加材质球强制让其入包, 或者用**Shader Variant Collect**), 不然会找不到.

```C#
using System;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

[Serializable]
public class URPSSAOSettings
{
	...
}

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

### **2.3 URPSSAORenderPass**

然后就再看**RenderPass**.

#### **2.3.1 构造函数**

这里先看构造函数
因为我这里是抄写的,比较符合我自己的代码习惯,而且还是一步一步慢慢填充的,所以跟原来的代码不一样.但是大体上的思想基本一致.
比如说**ProfilingSampler.Get(URPProfileId.SSAO)**外部获取不了,我这里用**k_tag**来自己创建.
再比如**isRendererDeferred**判断是否为延迟渲染.因为 **renderer.renderingMode** 是internal, 所以没有办法判断, 只能先写成false. 之后再在settings里面加个bool用于代替.

```C#
using System;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

public class URPSSAORenderPass : ScriptableRenderPass
{
	// private ProfilingSampler m_ProfilingSampler = ProfilingSampler.Get(URPProfileId.SSAO);
	private const string k_tag = "URPSSAO";

	// Private Variables
	private URPSSAOSettings m_CurrentSettings;

	// Properties
	// 是internal 虽然也可以用反射
	// m_Renderer is UniversalRenderer renderer && renderer.renderingMode == RenderingMode.Deferred;
	private bool isRendererDeferred => false; 

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

#### **2.3.2 Setup**

然后再看看每帧执行的**Setup**.
把**Feature**的变量传递进去,记录保存.
根据变量决定是否要开启SSAO, 渲染队列, 和需要的场景信息.
(URP2021**ConfigureInput**终于支持**Motion Vector**)

```C#
...

private Material m_Material;
private ScriptableRenderer m_Renderer;
private URPSSAOSettings m_CurrentSettings;

...

internal URPSSAORenderPass()
{
	...
}

internal bool Setup(URPSSAOSettings featureSettings, ScriptableRenderer renderer, Material material)
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

public override void Execute(ScriptableRenderContext context, ref RenderingData renderingData)
{
	...
}

```

#### **2.3.3 Property**

为了后面对材质球属性设置省事,我们可以提前粘贴需要的全部属性. Ctrl+C+V一下,啪很快啊.
 
```C#
private const string k_tag = "URPSSAO";

#region Property

public static readonly int s_SourceSize = Shader.PropertyToID("_SourceSize");


private static readonly int s_BaseMapID = Shader.PropertyToID("_BaseMap");
private static readonly int s_SSAOParamsID = Shader.PropertyToID("_SSAOParams");
private static readonly int s_SSAOTexture1ID = Shader.PropertyToID("_SSAO_OcclusionTexture1");
private static readonly int s_SSAOTexture2ID = Shader.PropertyToID("_SSAO_OcclusionTexture2");
private static readonly int s_SSAOTexture3ID = Shader.PropertyToID("_SSAO_OcclusionTexture3");
private static readonly int s_SSAOTextureFinalID = Shader.PropertyToID("_SSAO_OcclusionTexture");
private static readonly int s_CameraViewXExtentID = Shader.PropertyToID("_CameraViewXExtent");
private static readonly int s_CameraViewYExtentID = Shader.PropertyToID("_CameraViewYExtent");
private static readonly int s_CameraViewZExtentID = Shader.PropertyToID("_CameraViewZExtent");
private static readonly int s_ProjectionParams2ID = Shader.PropertyToID("_ProjectionParams2");
private static readonly int s_CameraViewProjectionsID = Shader.PropertyToID("_CameraViewProjections");
private static readonly int s_CameraViewTopLeftCornerID = Shader.PropertyToID("_CameraViewTopLeftCorner");

#endregion

// Private Variables
private Material m_Material;
...

internal URPSSAORenderPass()
{
	...
}

```

#### **2.3.4 OnCameraSetup**

我们这里按照渲染逻辑顺序依次说明.不过这里只写override的方法,比如**Configure**,**FrameCleanup**都没有重写就跳过顺序说明了.
当成功加入到渲染队列之后,就是先执行**OnCameraSetup**.
**OnCameraSetup**这里主要是对材质球的属性设置.

先写ssaoParams的设置.
```C#

internal bool Setup(URPSSAOSettings featureSettings, ScriptableRenderer renderer,
	Material material)
{
	...
}

public override void OnCameraSetup(CommandBuffer cmd, ref RenderingData renderingData)
{
	RenderTextureDescriptor cameraTargetDescriptor = renderingData.cameraData.cameraTargetDescriptor;
	int downsampleDivider = m_CurrentSettings.Downsample ? 2 : 1;

	// Update SSAO parameters in the material
	Vector4 ssaoParams = new Vector4(
		m_CurrentSettings.Intensity, // Intensity
		m_CurrentSettings.Radius, // Radius
		1.0f / downsampleDivider, // Downsampling
		m_CurrentSettings.SampleCount // Sample count
	);
	m_Material.SetVector(s_SSAOParamsID, ssaoParams);

}
```

然后就是摄像机属性的设置. 
2021新加了XR的支持.**renderingData.cameraData.xr**因为是**internal**,我这里改成**renderingData.cameraData.xrRendering**. 因为我也没有VR已经不开发VR了(不会还有人在开发VR,不会吧不会吧), 根本不关心这个API hhh.
XR主要是多了一个eye,让其成为**VectorArray**.但是总体没有什么大变化.
这里主要的计算就是把**proj空间**下的**最远的极值点**(最远左上点,最远右上点,最远右下点,最远中心点), 转换到**world空间**坐标. 然后记录左上,XY方向,中心方向.


```C#

...

private URPSSAOSettings m_CurrentSettings;

private Vector4[] m_CameraTopLeftCorner = new Vector4[2];
private Vector4[] m_CameraXExtent = new Vector4[2];
private Vector4[] m_CameraYExtent = new Vector4[2];
private Vector4[] m_CameraZExtent = new Vector4[2];
private Matrix4x4[] m_CameraViewProjections = new Matrix4x4[2];

...

public override void OnCameraSetup(CommandBuffer cmd, ref RenderingData renderingData)
{
	...
	m_Material.SetVector(s_SSAOParamsID, ssaoParams);

	
#if ENABLE_VR && ENABLE_XR_MODULE
	//renderingData.cameraData.xr.enabled && renderingData.cameraData.xr.singlePassEnabled ->  renderingData.cameraData.xrRendering  
	int eyeCount = renderingData.cameraData.xrRendering ? 2 : 1;
#else
	int eyeCount = 1;
#endif
	for (int eyeIndex = 0; eyeIndex < eyeCount; eyeIndex++)
	{
		Matrix4x4 view = renderingData.cameraData.GetViewMatrix(eyeIndex);
		Matrix4x4 proj = renderingData.cameraData.GetProjectionMatrix(eyeIndex);
		m_CameraViewProjections[eyeIndex] = proj * view;

		// camera view space without translation, used by SSAO.hlsl ReconstructViewPos() to calculate view vector.
		Matrix4x4 cview = view;
		cview.SetColumn(3, new Vector4(0.0f, 0.0f, 0.0f, 1.0f));
		Matrix4x4 cviewProj = proj * cview;
		Matrix4x4 cviewProjInv = cviewProj.inverse;

		Vector4 topLeftCorner = cviewProjInv.MultiplyPoint(new Vector4(-1, 1, -1, 1));
		Vector4 topRightCorner = cviewProjInv.MultiplyPoint(new Vector4(1, 1, -1, 1));
		Vector4 bottomLeftCorner = cviewProjInv.MultiplyPoint(new Vector4(-1, -1, -1, 1));
		Vector4 farCentre = cviewProjInv.MultiplyPoint(new Vector4(0, 0, 1, 1));
		m_CameraTopLeftCorner[eyeIndex] = topLeftCorner;
		m_CameraXExtent[eyeIndex] = topRightCorner - topLeftCorner;
		m_CameraYExtent[eyeIndex] = bottomLeftCorner - topLeftCorner;
		m_CameraZExtent[eyeIndex] = farCentre;
	}

	m_Material.SetVector(s_ProjectionParams2ID,
		new Vector4(1.0f / renderingData.cameraData.camera.nearClipPlane, 0.0f, 0.0f, 0.0f));
	m_Material.SetMatrixArray(s_CameraViewProjectionsID, m_CameraViewProjections);
	m_Material.SetVectorArray(s_CameraViewTopLeftCornerID, m_CameraTopLeftCorner);
	m_Material.SetVectorArray(s_CameraViewXExtentID, m_CameraXExtent);
	m_Material.SetVectorArray(s_CameraViewYExtentID, m_CameraYExtent);
	m_Material.SetVectorArray(s_CameraViewZExtentID, m_CameraZExtent);
}
```

再后面就是一些**keyword**设置.
添加关键字string并且设置.
比如摄像机类型, Normal采样质量, 用Depth还是DepthNormal图.

```C#

private const string k_tag = "URPSSAO";

#region Keyword

private const string k_ScreenSpaceOcclusion = "_SCREEN_SPACE_OCCLUSION";
private const string k_SSAOTextureName = "_ScreenSpaceOcclusionTexture";
private const string k_SSAOAmbientOcclusionParamName = "_AmbientOcclusionParam";

private const string k_OrthographicCameraKeyword = "_ORTHOGRAPHIC";
private const string k_NormalReconstructionLowKeyword = "_RECONSTRUCT_NORMAL_LOW";
private const string k_NormalReconstructionMediumKeyword = "_RECONSTRUCT_NORMAL_MEDIUM";
private const string k_NormalReconstructionHighKeyword = "_RECONSTRUCT_NORMAL_HIGH";
private const string k_SourceDepthKeyword = "_SOURCE_DEPTH";
private const string k_SourceDepthNormalsKeyword = "_SOURCE_DEPTH_NORMALS";

#endregion

#region Property
...
#endregion

...

public override void OnCameraSetup(CommandBuffer cmd, ref RenderingData renderingData)
{
	m_Material.SetVectorArray(s_CameraViewZExtentID, m_CameraZExtent);
	...

	// Update keywords
	CoreUtils.SetKeyword(m_Material, k_OrthographicCameraKeyword, renderingData.cameraData.camera.orthographic);

	URPSSAOSettings.DepthSource source = this.isRendererDeferred
		? URPSSAOSettings.DepthSource.DepthNormals
		: m_CurrentSettings.Source;

	if (source == URPSSAOSettings.DepthSource.Depth)
	{
		switch (m_CurrentSettings.NormalSamples)
		{
			case URPSSAOSettings.NormalQuality.Low:
				CoreUtils.SetKeyword(m_Material, k_NormalReconstructionLowKeyword, true);
				CoreUtils.SetKeyword(m_Material, k_NormalReconstructionMediumKeyword, false);
				CoreUtils.SetKeyword(m_Material, k_NormalReconstructionHighKeyword, false);
				break;
			case URPSSAOSettings.NormalQuality.Medium:
				CoreUtils.SetKeyword(m_Material, k_NormalReconstructionLowKeyword, false);
				CoreUtils.SetKeyword(m_Material, k_NormalReconstructionMediumKeyword, true);
				CoreUtils.SetKeyword(m_Material, k_NormalReconstructionHighKeyword, false);
				break;
			case URPSSAOSettings.NormalQuality.High:
				CoreUtils.SetKeyword(m_Material, k_NormalReconstructionLowKeyword, false);
				CoreUtils.SetKeyword(m_Material, k_NormalReconstructionMediumKeyword, false);
				CoreUtils.SetKeyword(m_Material, k_NormalReconstructionHighKeyword, true);
				break;
			default:
				throw new ArgumentOutOfRangeException();
		}
	}

	switch (source)
	{
		case URPSSAOSettings.DepthSource.DepthNormals:
			CoreUtils.SetKeyword(m_Material, k_SourceDepthKeyword, false);
			CoreUtils.SetKeyword(m_Material, k_SourceDepthNormalsKeyword, true);
			break;
		default:
			CoreUtils.SetKeyword(m_Material, k_SourceDepthKeyword, true);
			CoreUtils.SetKeyword(m_Material, k_SourceDepthNormalsKeyword, false);
			break;
	}
}

```

最后的最后就是 **descriptors**创建和设置, **RenderTargetIdentifier**的初始化, RT的创建, 和画布的输入.
因为AO的结果图是一个0-1的黑白图,所以单通道的**R8**就可以了.不过可能存在一些设备不支持,就用**ARGB32**.
为了效果好,这里RT的用**FilterMode**用**Bilinear**.
最后的画布输入,如果是**AfterOpaque**, 就画在Color RT上类似于贴上去, 否则就创建一个RT, 物体着色的时候进行采样, 让其变暗.
**RenderTargetIdentifier** , 是和**ID**进行绑定的. 在后面渲染的时候用到, 作用是避免每次传递的时候都进行创建, 所以在这里先初始化.


```C#
...

#region Property
...
#endregion

private bool m_SupportsR8RenderTextureFormat = SystemInfo.SupportsRenderTextureFormat(RenderTextureFormat.R8);

private Material m_Material;

...
private Matrix4x4[] m_CameraViewProjections = new Matrix4x4[2];

private RenderTextureDescriptor m_AOPassDescriptor;
private RenderTextureDescriptor m_BlurPassesDescriptor;
private RenderTextureDescriptor m_FinalDescriptor;

private RenderTargetIdentifier m_SSAOTexture1Target = new(s_SSAOTexture1ID, 0, CubemapFace.Unknown, -1);
private RenderTargetIdentifier m_SSAOTexture2Target = new(s_SSAOTexture2ID, 0, CubemapFace.Unknown, -1);
private RenderTargetIdentifier m_SSAOTexture3Target = new(s_SSAOTexture3ID, 0, CubemapFace.Unknown, -1);
private RenderTargetIdentifier m_SSAOTextureFinalTarget = new(s_SSAOTextureFinalID, 0, CubemapFace.Unknown, -1);

// Properties
//m_Renderer is UniversalRenderer renderer && renderer.renderingMode == RenderingMode.Deferred;
private bool isRendererDeferred => false;

internal URPSSAORenderPass()
{
	...
}

public override void OnCameraSetup(CommandBuffer cmd, ref RenderingData renderingData)
{
	...
	
	switch (source)
	{
		...
	}

	// Set up the descriptors
	RenderTextureDescriptor descriptor = cameraTargetDescriptor;
	descriptor.msaaSamples = 1;
	descriptor.depthBufferBits = 0;

	m_AOPassDescriptor = descriptor;
	m_AOPassDescriptor.width /= downsampleDivider;
	m_AOPassDescriptor.height /= downsampleDivider;
	m_AOPassDescriptor.colorFormat = RenderTextureFormat.ARGB32;

	m_BlurPassesDescriptor = descriptor;
	m_BlurPassesDescriptor.colorFormat = RenderTextureFormat.ARGB32;

	m_FinalDescriptor = descriptor;
	m_FinalDescriptor.colorFormat =
		m_SupportsR8RenderTextureFormat ? RenderTextureFormat.R8 : RenderTextureFormat.ARGB32;

	// Get temporary render textures
	cmd.GetTemporaryRT(s_SSAOTexture1ID, m_AOPassDescriptor, FilterMode.Bilinear);
	cmd.GetTemporaryRT(s_SSAOTexture2ID, m_BlurPassesDescriptor, FilterMode.Bilinear);
	cmd.GetTemporaryRT(s_SSAOTexture3ID, m_BlurPassesDescriptor, FilterMode.Bilinear);
	cmd.GetTemporaryRT(s_SSAOTextureFinalID, m_FinalDescriptor, FilterMode.Bilinear);

	// Configure targets and clear color
	ConfigureTarget(m_CurrentSettings.AfterOpaque ? m_Renderer.cameraColorTarget : s_SSAOTexture2ID);
	ConfigureClear(ClearFlag.None, Color.white);
}

```

#### **2.3.5 Execute**

之后就是执行渲染了. 先写一个基础的框架.

```C#

 public override void Execute(ScriptableRenderContext context, ref RenderingData renderingData)
{
	if (m_Material == null)
	{
		Debug.LogErrorFormat("{0}.Execute(): Missing material. ScreenSpaceAmbientOcclusion pass will not execute. Check for missing reference in the renderer resources.", GetType().Name);
		return;
	}

	CommandBuffer cmd = CommandBufferPool.Get();
	using (new ProfilingScope(cmd, m_ProfilingSampler))
	{
		//TODO:
	}

	context.ExecuteCommandBuffer(cmd);
	CommandBufferPool.Release(cmd);
}
```

然后填充框架.这里是先设置**Keyword**和**SourceSize**.
**AfterOpaque**决定是由哪种方式采样表现AO效果.所以需要设置一个关键字**k_ScreenSpaceOcclusion**在shader中进行开关. 关键字重置在后面的**OnCameraCleanup**中完成.


```C#

public override void Execute(ScriptableRenderContext context, ref RenderingData renderingData)
{
	...

	using (new ProfilingScope(cmd, profilingSampler))
	{
		if (!m_CurrentSettings.AfterOpaque)
		{
			//ShaderKeywordStrings.ScreenSpaceOcclusion 拷贝出来
			CoreUtils.SetKeyword(cmd, k_ScreenSpaceOcclusion, true);
		}	
	}

	...
}



```

再后面就是渲染AO了. 在此之前 先写 **Enum ShaderPasses** 和 三个Render的公共方法.
**Enum ShaderPasses**, 需要和shader pass index 对应.
因为**SetSourceSize**是**interal**, 所以我这里直接拷贝出来了. 主要作用就是 传递画布尺寸(考虑动态画布缩放)到Shader中.
**Render**, 设置RT, 全屏绘制某个pass. 因为是全部覆盖的后处理绘制, 所以不关心(**DontCare**)输入的颜色 和 depth, 只需要**Store**输出的颜色就好了.
**RenderAndSetBaseMap**, 同上, 并且多传入一个BaseMap.

```C#

public class URPSSAORenderPass : ScriptableRenderPass
{
	private enum ShaderPasses
	{
		AO = 0,
		BlurHorizontal = 1,
		BlurVertical = 2,
		BlurFinal = 3,
		AfterOpaque = 4
	}
	
	
	private const string k_tag = "URPSSAO";

	...

	public override void Execute(ScriptableRenderContext context, ref RenderingData renderingData)
	{
		...
	}

	//PostProcessUtils.SetSourceSize是internal,所以拷贝出来了
	private void SetSourceSize(CommandBuffer cmd, RenderTextureDescriptor desc)
	{
		float width = desc.width;
		float height = desc.height;
		if (desc.useDynamicScale)
		{
			width *= ScalableBufferManager.widthScaleFactor;
			height *= ScalableBufferManager.heightScaleFactor;
		}

		cmd.SetGlobalVector(s_SourceSize, new Vector4(width, height, 1.0f / width, 1.0f / height));
	}

	private void Render(CommandBuffer cmd, RenderTargetIdentifier target, ShaderPasses pass)
	{
		cmd.SetRenderTarget(
			target,
			RenderBufferLoadAction.DontCare,
			RenderBufferStoreAction.Store,
			target,
			RenderBufferLoadAction.DontCare,
			RenderBufferStoreAction.DontCare
		);
		cmd.DrawMesh(RenderingUtils.fullscreenMesh, Matrix4x4.identity, m_Material, 0, (int)pass);
	}

	private void RenderAndSetBaseMap(CommandBuffer cmd, RenderTargetIdentifier baseMap, RenderTargetIdentifier target, ShaderPasses pass)
	{
		cmd.SetGlobalTexture(s_BaseMapID, baseMap);
		Render(cmd, target, pass);
	}
}

```

然后渲染.
设置分辨率(可能是半分辨率), 渲染AO, 然后横着模糊.
重新设置全分辨率尺寸, 竖着模糊. 稍微处理一下输出FinalRT.
设置FinalRT和AO参数.
因为**AfterOpaque**时, 是类似于贴上去的. 所以还需要设置RT进行全屏带blend的绘制.

```C#

public override void Execute(ScriptableRenderContext context, ref RenderingData renderingData)
{
	...

	CommandBuffer cmd = CommandBufferPool.Get();
	using (new ProfilingScope(cmd, profilingSampler))
	{
		if (!m_CurrentSettings.AfterOpaque)
		{
			...
		}

		SetSourceSize(cmd, m_AOPassDescriptor);
		// Execute the SSAO
		Render(cmd, m_SSAOTexture1Target, ShaderPasses.AO);

		// Execute the Blur Passes
		RenderAndSetBaseMap(cmd, m_SSAOTexture1Target, m_SSAOTexture2Target, ShaderPasses.BlurHorizontal);

		SetSourceSize(cmd, m_BlurPassesDescriptor);
		RenderAndSetBaseMap(cmd, m_SSAOTexture2Target, m_SSAOTexture3Target, ShaderPasses.BlurVertical);
		RenderAndSetBaseMap(cmd, m_SSAOTexture3Target, m_SSAOTextureFinalTarget, ShaderPasses.BlurFinal);

		// Set the global SSAO texture and AO Params
		cmd.SetGlobalTexture(k_SSAOTextureName, m_SSAOTextureFinalTarget);
		cmd.SetGlobalVector(k_SSAOAmbientOcclusionParamName, new Vector4(0f, 0f, 0f, m_CurrentSettings.DirectLightingStrength));

		// If true, SSAO pass is inserted after opaque pass and is expected to modulate lighting result now.
		if (m_CurrentSettings.AfterOpaque)
		{
			// This implicitly also bind depth attachment. Explicitly binding m_Renderer.cameraDepthTarget does not work.
			cmd.SetRenderTarget(
				m_Renderer.cameraColorTarget,
				RenderBufferLoadAction.Load,
				RenderBufferStoreAction.Store
			);
			cmd.DrawMesh(RenderingUtils.fullscreenMesh, Matrix4x4.identity, m_Material, 0, (int)ShaderPasses.AfterOpaque);
		}

	}

	...
}

```

#### **2.3.5 OnCameraCleanup**

整个camera渲染完成, 重置参数, 清理临时RT.

```C#

public override void Execute(ScriptableRenderContext context, ref RenderingData renderingData)
{
	...
}

public override void OnCameraCleanup(CommandBuffer cmd)
{
	if (cmd == null)
	{
		throw new ArgumentNullException("cmd");
	}

	if (!m_CurrentSettings.AfterOpaque)
	{
		CoreUtils.SetKeyword(cmd, ShaderKeywordStrings.ScreenSpaceOcclusion, false);
	}

	cmd.ReleaseTemporaryRT(s_SSAOTexture1ID);
	cmd.ReleaseTemporaryRT(s_SSAOTexture2ID);
	cmd.ReleaseTemporaryRT(s_SSAOTexture3ID);
	cmd.ReleaseTemporaryRT(s_SSAOTextureFinalID);
}

//PostProcessUtils.SetSourceSize是internal,所以拷贝出来了
private void SetSourceSize(CommandBuffer cmd, RenderTextureDescriptor desc)
{
	...
}

```

#### **2.3.6 Deferred设置**

因为我们获取不到Deferred, 所以需要自己添加bool, 通过Editor反射来设置.

打开**URPSSAORenderFeature.cs**, 修改 **class URPSSAOSettings**

```C#

[Serializable]
public class URPSSAOSettings
{
	...

	// Parameters
	[SerializeField] public bool IsDeferred = false;
	[SerializeField] public bool Downsample = false;
	...
}

[DisallowMultipleRendererFeature]
[Tooltip(
	"The Ambient Occlusion effect darkens creases, holes, intersections and surfaces that are close to each other.")]
public class URPSSAORenderFeature : ScriptableRendererFeature
{
	...
}

```

最后返回**URPSSAORenderPass.cs**, 修改**isRendererDeferred**
```C#

public class URPSSAORenderPass : ScriptableRenderPass
{
	...
	private RenderTargetIdentifier m_SSAOTextureFinalTarget = new(s_SSAOTextureFinalID, 0, CubemapFace.Unknown, -1);

	// Properties
	//m_Renderer is UniversalRenderer renderer && renderer.renderingMode == RenderingMode.Deferred;
	private bool isRendererDeferred => m_CurrentSettings.IsDeferred;

	internal URPSSAORenderPass()
	{
		...
	}

	...
}

```

### **2.4 InspectorGUI**








//TODO:反射设置延迟
//TODO:Shader