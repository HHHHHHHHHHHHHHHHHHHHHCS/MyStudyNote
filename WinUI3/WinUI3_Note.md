### 如果 Unpackaged 启动报错

https://stackoverflow.com/questions/70100728/microsoft-ui-xaml-dll-is-unable-to-load

在 xxxx.csproj  的 PropertyGroup 中添加 下面这句话

```XML

<WindowsAppSDKSelfContained>true</WindowsAppSDKSelfContained>

```


### Smaple Demo

https://apps.microsoft.com/store/detail/winui-3-gallery/9P3JFPWWDZRC?hl=en-us&gl=us

https://zhuanlan.zhihu.com/p/446104191