### 如果 Unpackaged 启动报错

https://stackoverflow.com/questions/70100728/microsoft-ui-xaml-dll-is-unable-to-load

在 xxxx.csproj  的 PropertyGroup 中添加 下面这句话

```XML

<WindowsAppSDKSelfContained>true</WindowsAppSDKSelfContained>

```


### Smaple Demo

https://apps.microsoft.com/store/detail/winui-3-gallery/9P3JFPWWDZRC?hl=en-us&gl=us

https://apps.microsoft.com/store/detail/winui-2-gallery/9MSVH128X2ZT

https://zhuanlan.zhihu.com/p/446104191

https://github.com/Scighost/WinUI3Keng

