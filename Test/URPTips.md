### 禁止debug提醒
[System.Diagnostics.CodeAnalysis.SuppressMessage("Microsoft.Performance", "CA1812")]



### 获取位置 创建并且 选中物体
```C#
[System.Diagnostics.CodeAnalysis.SuppressMessage("Microsoft.Performance", "CA1812")]
internal class CreateUniversalRendererAsset : EndNameEditAction
{
	public override void Action(int instanceId, string pathName, string resourceFile)
	{
		var instance =
			MyUniversalRenderPipelineAsset.CreateRendererAsset(pathName, MyRendererType.UniversalRenderer,
					false) as
				MyUniversalRendererData;
		Selection.activeObject = instance;
	}
}

[MenuItem("Assets/Create/MyRendering/URP Universal Renderer",
	priority = CoreUtils.Sections.section3 + CoreUtils.Priorities.assetsCreateRenderingMenuPriority + 2)]
private static void CreateUniversalRendererData()
{
	ProjectWindowUtil.StartNameEditingIfProjectWindowExists(0, CreateInstance<CreateUniversalRendererAsset>(),
		"CustomUniversalRendererData.asset", null, null);
}
```


### 加载序列化
```C#
string resourcePath = AssetDatabase.GUIDToAssetPath(editorResourcesGUID);
var objs = InternalEditorUtility.LoadSerializedFileAndForget(resourcePath);
m_EditorResourcesAsset = objs != null && objs.Length > 0
	? objs.First() as MyUniversalRenderPipelineEditorResources
	: null;
```


### Editor API
EditorApplication.delayCall
EditorUtility.InstanceIDToObject



### 管线Shader GlobalRenderPipeline
Shader.globalRenderPipeline = "UniversalPipeline";



### SceneViewDrawMode
MySceneViewDrawMode.SetupDrawMode();


### Marshal.SizeOf
C# 获取对象 大小 Marshal.SizeOf (sizeof 只能在不安全的上下文中使用)


### lightUseLinear  RenderPipelineBatching  RenderingLayerMask
GraphicsSettings.lightsUseLinearIntensity = (QualitySettings.activeColorSpace == ColorSpace.Linear);
//计算Light的最终颜色时  使用该Light的色温 https://docs.unity3d.com/cn/2017.1/ScriptReference/Rendering.GraphicsSettings-lightsUseColorTemperature.html
GraphicsSettings.lightsUseColorTemperature = true;
GraphicsSettings.useScriptableRenderPipelineBatching = asset.useSRPBatcher;
GraphicsSettings.defaultRenderingLayerMask = k_DefaultRenderingLayerMask;

### 获取当前的RenderPipeline
GraphicsSettings.currentRenderPipeline as MyUniversalRenderPipelineAsset


### Projection Matrix Y翻转
struct CameraData

public Matrix4x4 GetGPUProjectionMatrix(int viewIndex = 0)
{
	return GL.GetGPUProjectionMatrix(GetProjectionMatrix(viewIndex), IsCameraProjectionMatrixFlipped());
}


### 从前到后绘制和HSR
MyUniversalRenderPipeline.InitializeStackedCameraData

var commonOpaqueFlags = SortingCriteria.CommonOpaque;
var noFrontToBackOpaqueFlags = SortingCriteria.SortingLayer | SortingCriteria.RenderQueue |
								SortingCriteria.OptimizeStateChanges | SortingCriteria.CanvasOrder;
bool hasHSRGPU = SystemInfo.hasHiddenSurfaceRemovalOnGPU;
bool canSkipFrontToBackSorting = (baseCamera.opaqueSortMode == OpaqueSortMode.Default && hasHSRGPU) ||
									baseCamera.opaqueSortMode == OpaqueSortMode.NoDistanceSort;

cameraData.defaultOpaqueSortFlags =
	canSkipFrontToBackSorting ? noFrontToBackOpaqueFlags : commonOpaqueFlags;


### HDR格式
https://baddogzz.github.io/2021/01/07/URP-HDR/
MyUniversalRenderPipeline.MakeRenderTextureGraphicsFormat
	GraphicsFormat hdrFormat;
	if (!needsAlpha && RenderingUtils.SupportsGraphicsFormat(GraphicsFormat.B10G11R11_UFloatPack32, FormatUsage.Linear | FormatUsage.Render))
		hdrFormat = GraphicsFormat.B10G11R11_UFloatPack32;
	else if (RenderingUtils.SupportsGraphicsFormat(GraphicsFormat.R16G16B16A16_SFloat, FormatUsage.Linear | FormatUsage.Render))
		hdrFormat = GraphicsFormat.R16G16B16A16_SFloat;
	else
		hdrFormat = SystemInfo.GetGraphicsFormat(DefaultFormat.HDR); // This might actually be a LDR format on old devices.

上述代码除了对纹理格式的支持判断以外，还有一个 needAlpha 的判断，如果需要 A通道，就用 ARGBHalf，否则，就用 R11G11B10。
Graphics.preserveFramebufferAlpha  //PlayerSettings 可以设置

### 得到默认的格式
SystemInfo.GetGraphicsFormat(DefaultFormat.LDR)