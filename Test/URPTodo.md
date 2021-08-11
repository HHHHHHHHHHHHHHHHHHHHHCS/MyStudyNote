### relod  Package.Builtin/root
可能会导致找不到   他可能是用shader.find/AssetDatabase.LoadAssetAtPath
不过也可以直接先用package的shader 和 asset
但是也也有可能序列化失败, 不过可以添加转换做个暂时的

搭配使用
[ReloadGroup],[Reload],ResourceReloader.ReloadAllNullIn(instance, MyUniversalRenderPipelineAsset.packagePath); 

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
