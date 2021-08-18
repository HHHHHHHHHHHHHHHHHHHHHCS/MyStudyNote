### relod  Package.Builtin/root
可能会导致找不到   他可能是用shader.find/AssetDatabase.LoadAssetAtPath
不过也可以直接先用package的shader 和 asset
但是也也有可能序列化失败, 不过可以添加转换做个暂时的

搭配使用
[ReloadGroup],[Reload],ResourceReloader.ReloadAllNullIn(instance, MyUniversalRenderPipelineAsset.packagePath); 



### editor ui 还没有写



### GetSettingsForRenderPipeline
GraphicsSettings.GetSettingsForRenderPipeline<UniversalRenderPipeline>() as UniversalRenderPipelineGlobalSettings;



### TODO:
My XRSystem系统还没有支持
My DecalProjector
My m_DebugDisplaySettingsUI