简单的RayTrace_CPU
=================

(Github正常排版: [简单的RayTrace_CPU](https://github.com/HHHHHHHHHHHHHHHHHHHHHCS/MyStudyNote/blob/main/MyNote/%E7%AE%80%E5%8D%95%E7%9A%84RayTrace_CPU.md))

------------------------

文章有点长,配了目录. 着实不知道cat大佬文章那种代码高亮和底色格式怎么弄的.现在这样写,看着有点乱.

- [简单的RayTrace_CPU](#简单的raytrace_cpu)
	- [**0.原因**](#0原因)
	- [**1.基础配置**](#1基础配置)
	- [**2.工具类准备**](#2工具类准备)
	- [**3.射线和球相交**](#3射线和球相交)
	- [**4.材质**](#4材质)
	- [**5.数据准备**](#5数据准备)
	- [**6.射线**](#6射线)
	- [**7.基础颜色**](#7基础颜色)
	- [**8.基础效果**](#8基础效果)
	- [**9.自发光**](#9自发光)
	- [**10.其它**](#10其它)
		- [**10.1.动画**](#101动画)
		- [**10.2.主线程**](#102主线程)
		- [**10.3.性能现实**](#103性能现实)

-----------------

## **0. 原因**

&emsp;&emsp; 看到gayhub上有一个项目,抄着学习一下(jiu shi wan),项目地址:[ToyPathTracer](https://github.com/aras-p/ToyPathTracer).

效果虽然不是很好,而且也没有什么高大上的东西,甚至都只有球的计算,但是拿来入门学习还是够用的.里面还有C++和C#的案例,这里就拿Unity来举个栗子,比较容易理解也比较直观.

洛城大神的两篇可以快速了解基础原理.

[一篇光线追踪的入门](https://zhuanlan.zhihu.com/p/41269520)

[光线追踪的QA](https://zhuanlan.zhihu.com/p/51493136)

当然还有光追A Week三件套.顺便安利一下闫老师的Games101讲的更详细,而且还搭配逐步的练习.PS:202也出了,yyds!

下图分别是C++,Unity+Job,纯C#(图三和四).效果基本都差不多,但是效率差很大.不过Job的效率居然比想象中的强大.

![CPURayTrace_0](Images/CPURayTrace_0.png)
![CPURayTrace_1](Images/CPURayTrace_1.jpg)
![CPURayTrace_2](Images/CPURayTrace_2.jpg)
![CPURayTrace_3](Images/CPURayTrace_3.jpg)

CPU都被拉满了,比博人传都要燃啊,堪比献给未来的游戏--某剑六,希望七不要拉胯了,拉胯了就说明别人是CPU光追游戏!!!

![CPURayTrace_10](Images/CPURayTrace_10.jpg)

不过也有解决办法(doge)

![CPURayTrace_11](Images/CPURayTrace_11.jpg)

回归正题其实学光追还有一个原因,就是很多东西光栅化的确很难办到(但是这个demo只讲简单的光追学习).

比如这个[网站](https://www.imaginationtech.com/blog/hybrid-rendering-for-real-time-lighting/)就举了一些例子,对比说明了光追和光栅化的一些区别.

比如说雨伞是可以轻微透光的,当然光栅化也可以用再次渲染一个shadowmap实现两个shadow的叠加.

![CPURayTrace_12](Images/CPURayTrace_12.gif)

还有曲面产生的自发光效果.遥想Unity当年面片自发光还要离线呢!

![CPURayTrace_13](Images/CPURayTrace_13.png)

再比如你撑着遮阳伞着伞走在马路上.伞的内部其实是会被来自地砖的光照亮的.如果按照shadowmap的原理内部应该是暗的,但是实际上会被地砖的反射光照亮.虽然也可以添加**Reflection Probe**来解决,或者进行**Screen Space Reflection**,但是效果比较一般.

![CPURayTrace_14](Images/CPURayTrace_14.jpg)

-----------------

## **1. 基础配置**

&emsp;&emsp; 项目需要安装Packages:Burst,Jobs,Mathematics.

创建一个**RawImage**,设置为全屏幕大小,用于显示最后的效果.当然也可以用**CommandBuffer.DrawFullScreen**或者**Graphics.Blit**都可以.这里用UI,首先是偷懒,第二是确保不会被后处理/颜色校正/颜色转换.

![CPURayTrace_4](Images/CPURayTrace_4.png)

创建一个C# **CPURayTracingTest.cs**

```C#
using System;
using System.Diagnostics;
using Unity.Collections;
using UnityEngine;
using UnityEngine.UI;


public class CPURayTracingTest : MonoBehaviour
{
	public int screenWidth, screenHeight;

	public RawImage uiImage;
}
```

挂载给摄像机,并且把刚才的**RawImage**给**uiImage**进行赋值.**screenWidth screenHeight** 给960和540.(忽略这个Text组件,它是后面的)

屏幕尺寸这里建议给小一点,为了后面方便快速呈现效果.(当然银河电脑当我没有话说!)因为一个像素会发射很多的光线进行大量的计算,所以给的点越少计算量越少,但是效果越差.

![CPURayTrace_5](Images/CPURayTrace_5.png)

**RawImage**的图片需要**Texture2D**(**Texture2D**需要申请为Linear Color Space, 不过写成false对最终渲染的画面也没有影响),而**Texture2D**的颜色需要**Color Buffer**来填充数据.

**Color Buffer**说白了就是一堆**Color**(需要屏幕像素数量的Color即width*height),便可以直接用**NativeArray<Color>t**来代替.(因为是长生命周期,所以用Allocator.Persistent. Allocator不知道的可以点击[Native Container Allocator](https://blog.csdn.net/lrh3025/article/details/102869011))

创建**Texture2D**和**NativeArray<Color>**,对其进行初始化设置.

因为**Color Buffer**每帧数都要做计算更新,所以**Texture2D**需要每帧数回读**Color Buffer**,那便在**Update**进行**Texture2D.LoadRawTextureData**.

最后别忘了在脚本销毁的时候需要释放**NativeArray<Color>**.

这样一来基础的配置就完成了.

```C#
public class CPURayTracingTest : MonoBehaviour
{
	....

	private Texture2D backBufferTex;
	private NativeArray<Color> backBuffer;

	private void Start()
	{
		int width = screenWidth; //Screen.width;
		int height = screenHeight; // Screen.height;

		backBufferTex = new Texture2D(width, height, TextureFormat.RGBAFloat, false, true);
		backBuffer = new NativeArray<Color>(width * height, Allocator.Persistent);
		for (int i = 0; i < backBuffer.Length; i++)
		{
			backBuffer[i] = new Color(0, 0, 0, 1);
		}

		uiImage.texture = backBufferTex;
	}

	private void OnDestroy()
	{
		backBuffer.Dispose();
	}

	private void Update()
	{
		backBufferTex.LoadRawTextureData(backBuffer);
		backBufferTex.Apply();
	}
}
```

-----------------

## **2. 工具类准备**

&emsp;&emsp; 在做光追的时候,先要提前准备一些结构体和求交计算.

创建一个static class**CPURayTracingMathUtil.cs**.为了后面写代码方便用**static**方法导入**Mathematics**.

```C#
using Unity.Collections;
using Unity.Collections.LowLevel.Unsafe;
using Unity.Mathematics;
using static Unity.Mathematics.math;

public static class CPURayTracingMathUtil
{

}
```

先创建几个结构体用于储存数据.

射线:**Ray**,需要起始点**ori**和方向**dir**,射线上的某一个点可以表示为ori+dir*t,t>=0,t即距离

碰撞结果:**Hit**,用于一个射线碰撞到场景物体记录的信息结构体.碰撞的点**pos**,记录碰撞点的法线**normal**,射线走了多少距离**t**.

球:**Sphere**,球就是圆心位置**center**和半径**radius**.

```C#
...

public struct Ray
{
	public float3 ori;
	public float3 dir;

	public Ray(float3 o, float3 d)
		=> (ori, dir) = (o, d);

	public float3 PointAt(float t) => ori + dir * t;
}

public struct Hit
{
	public float3 pos;
	public float3 normal;
	public float t;
}

public struct Sphere
{
	public float3 center;
	public float radius;

	public Sphere(float3 c, float r)
		=> (center, radius) = (c, r);
}

public static class CPURayTracingMathUtil
{

}

```

再创建 **摄像机(Camera)** 结构体.

摄像机需要起始点**lookFrom**,看的方向**lookAt**,向上的方向**vup**默认float3(0,1,0),视场角**fov**(也就是俗称的底),屏幕宽高**aspect**,光圈大小**aperture**(虚化用),聚焦距离**focusDist**.(Games101-P19有超级详细的说明)

**aperture**值越大,代表光圈越大.因为镜片是薄棱镜,所以产生折射角度会越大,光线不会聚集到一起,最后图像会被模糊.下面的图可以看到效果,显而易见远处模糊.

![CPURayTrace_15](Images/CPURayTrace_15.jpg)
![CPURayTrace_16](Images/CPURayTrace_16.jpg)
![CPURayTrace_17](Images/CPURayTrace_17.jpg)
aperture = 0.5 * 0.2
![CPURayTrace_6](Images/CPURayTrace_6.jpg)
aperture = 0.1 * 0.2
![CPURayTrace_7](Images/CPURayTrace_7.jpg)

**focusDist**聚焦距离,正常改动影响不会很大.但是如果**aperture**值比较大的时候就很重要,它能确保聚焦距离对应的一块的图像是清晰的.

![CPURayTrace_18](Images/CPURayTrace_18.jpg)
![CPURayTrace_19](Images/CPURayTrace_19.png)

aperture = 1 * 0.2 , distToFocus = 3
![CPURayTrace_20](Images/CPURayTrace_20.jpg)
aperture = 1 * 0.2 , distToFocus = 6
![CPURayTrace_21](Images/CPURayTrace_21.jpg)

用传入的数据构建摄像机完成基础的属性.

```C#

...

public struct Sphere
{
	...
}

public struct Camera
{
	private float3 origin;
	private float3 lowerLeftCorner;
	private float3 horizontal;
	private float3 vertical;
	private float3 u, v, w;
	private float lensRadius;

	// vfov is top to bottom in degrees
	//aperture光圈大小 模糊用   focusDist是聚焦的距离
	public Camera(float3 lookFrom, float3 lookAt, float3 vup, float vfov, float aspect, float aperture, 
	float focusDist)
	{
		lensRadius = aperture / 2;
		float theta = vfov * PI / 180;
		float halfHeight = tan(theta / 2);
		float halfWidth = aspect * halfHeight;
		origin = lookFrom;
		w = normalize(lookFrom - lookAt);
		u = normalize(cross(vup, w));
		v = cross(w, u);
		lowerLeftCorner = origin - focusDist * (halfWidth * u + halfHeight * v + w);


		horizontal = 2 * halfWidth * focusDist * u;
		vertical = 2 * halfHeight * focusDist * v;
	}
}

public static class CPURayTracingMathUtil
{
}

```


因为光追是从相机点出发射向聚焦平面,所以我们还需要写一个方法用于得到射线.

因为存在光圈,即我们可能会得到虚化/模糊的图片.可以参考上面的图,其实就是没有完美成像在平面上.那么我们可以反过来想,可以让发出去的射线不会太规则,让其加点随机偏移和方向偏离,然后把得到的颜色平均,这样就可以得到虚化的效果了.

随机方向这块可以用别的方法替代(这里用ref传入是为了保证下一次的结果不一致),甚至可以用do-while.但是要确保要在圆/球的外面,且不能超过单位1的cube.因为在球内则可能值过小,如果是归一化,则分布的还不够随机过于密集.

```C#

public struct Camera
{
	...

	public Ray GetRay(float s, float t, ref uint state)
	{
		float3 rd = lensRadius * CPURayTracingMathUtil.RandomInUnitDisk(ref state);
		float3 offset = u * rd.x + v * rd.y;
		return new Ray(origin + offset,
			normalize(lowerLeftCorner + s * horizontal + t * vertical - origin - offset));
	}
}


public static class CPURayTracingMathUtil
{
	
	//Random
	//-------------------

	//生成随机数
	private static uint XorShift32(ref uint state)
	{
		uint x = state;
		x ^= x << 13;
		x ^= x >> 17;
		x ^= x << 15;
		state = x;
		return x;
	}

	//[0,1)
	public static float RandomFloat01(ref uint state)
	{
		// 0xFFFFFF => 16777215
		return (XorShift32(ref state) & 0xFFFFFF) / 16777216.0f;
	}

	public static float3 RandomInUnitDisk(ref uint state)
	{
		float3 p;
		// do
		// {
		// 	p = 2.0f * new float3(RandomFloat01(ref state), RandomFloat01(ref state), 0) - new float3(1, 1, 0);
		// } while (lengthsq(p) >= 1.0);
		// return p;

		var x = RandomFloat01(ref state);
		var y = RandomFloat01(ref state);

		float length = 1;
		float dx, dy;
		if (x == 0 && y == 0)
		{
			// return float3(2, 2, 0); // => float3(1,1,0)+float3(1,1,0);
			dx = 1;
			dy = 1;
		}
		else
		{
			float len = sqrt(x * x + y * y);
			dx = x / len;
			dy = y / len;

			if (x != 0 && y != 0)
			{
				float maxDis = min(y / x, x / y); //碰触到 x=1|y=1 的点的距离
				maxDis = sqrt(maxDis * maxDis + 1 * 1) - 1;
				length += maxDis * RandomFloat01(ref state);
			}
		}


		//象限
		var xx = RandomFloat01(ref state);
		if (xx < 0.25f) //第一象限
		{
		}
		else if (xx < 0.5f) //第二象限
		{
			dx *= -1;
		}
		else if (xx < 0.75f) //第三象限
		{
			dx *= -1;
			dy *= -1;
		}
		else //if (xx < 1f)//第四象限
		{
			dy *= -1;
		}

		p = float3(dx * length, dy * length, 0);


		return p;
	}

	public static float3 RandomInUnitSphere(ref uint state)
	{
		float3 p;
		// do
		// {
		// 	p = 2.0f * new float3(RandomFloat01(ref state), RandomFloat01(ref state), RandomFloat01(ref state)) -
		// 	    new float3(1, 1, 1);
		// } while (lengthsq(p) >= 1.0);
		// return p;

		var x = RandomFloat01(ref state);
		var y = RandomFloat01(ref state);
		var z = RandomFloat01(ref state);

		float length = 1;
		float dx, dy, dz;

		if (x == 0 && y == 0 && z == 0)
		{
			// return float3(2, 2, 2); // => float3(1,1,1)+float3(1,1,1);
			dx = 1;
			dy = 1;
			dz = 1;
		}
		else
		{
			float len = sqrt(x * x + y * y + z * z);
			dx = x / len;
			dy = y / len;
			dz = z / len;

			float a, b, c;
			float macD = max(max(x, y), z);
			a = x / macD;
			b = y / macD;
			c = z / macD;

			float maxDis = sqrt(a * a + b * b + c * c) - 1;
			length += maxDis * RandomFloat01(ref state);
		}


		//象限
		var xx = RandomFloat01(ref state);
		if (xx < 0.125f) //第一象限
		{
		}
		else if (xx < 0.25f) //第二象限
		{
			dx *= -1;
		}
		else if (xx < 0.375f) //第三象限
		{
			dx *= -1;
			dy *= -1;
		}
		else if (xx < 0.5f) //第四象限
		{
			dy *= -1;
		}

		if (xx < 0.625f) //第五象限
		{
			dz *= -1;
		}
		else if (xx < 0.75f) //第六象限
		{
			dx *= -1;
			dz *= -1;
		}
		else if (xx < 0.875f) //第七象限
		{
			dx *= -1;
			dy *= -1;
			dz *= -1;
		}
		else //if (xx < 1f)//第八象限
		{
			dy *= -1;
			dz *= -1;
		}

		p = float3(dx * length, dy * length, dz * length);


		return p;
	}

	public static float3 RandomUnitVector(ref uint state)
	{
		float z = RandomFloat01(ref state) * 2.0f - 1.0f;
		float a = RandomFloat01(ref state) * 2.0f * PI;
		float r = sqrt(1.0f - z * z);
		float x, y;
		sincos(a, out x, out y);
		return new float3(r * x, r * y, z);
	}
}

```

-----------------

## **3. 射线和球相交**

接下来就就是比较麻烦的射线和球的相交计算.

创建一个**struct SpheresSOA**在**CPURayTracingMathUtil.cs**.先添点属性用来储存全部球的信息.本来可以用**NativeArray<float4> XYZRadius**来记录,但是为了后面计算的方便快捷,就改成单独记录centerX,centerY,centerZ,radius. radius甚至可以提前计算好r*r和1/r,节约运算次数.

然后一组是4个,因为floatN最大是float4,开辟一个向上4取整的长度进行初始化.并且别忘记添加销毁代码.

```C#
...

public struct Sphere
{
	...
}

public struct SpheresSOA
{
	[ReadOnly] public NativeArray<float> centerX;
	[ReadOnly] public NativeArray<float> centerY;
	[ReadOnly] public NativeArray<float> centerZ;
	[ReadOnly] public NativeArray<float> sqRadius;
	[ReadOnly] public NativeArray<float> invRadius;

	public SpheresSOA(int len)
	{
		var simdLen = ((len + 3) / 4) * 4;
		centerX = new NativeArray<float>(simdLen, Allocator.Persistent);
		centerY = new NativeArray<float>(simdLen, Allocator.Persistent);
		centerZ = new NativeArray<float>(simdLen, Allocator.Persistent);
		sqRadius = new NativeArray<float>(simdLen, Allocator.Persistent);
		invRadius = new NativeArray<float>(simdLen, Allocator.Persistent);
		// set trailing data to "impossible sphere" state
		for (int i = len; i < simdLen; ++i)
		{
			centerX[i] = centerY[i] = centerZ[i] = float.MaxValue;
			sqRadius[i] = 0.0f;
			invRadius[i] = 0.0f;
		}
	}

	public void Dispose()
	{
		centerX.Dispose();
		centerY.Dispose();
		centerZ.Dispose();
		sqRadius.Dispose();
		invRadius.Dispose();
	}

	public void Update(Sphere[] src)
	{
		for (var i = 0; i < src.Length; i++)
		{
			ref Sphere s = ref src[i];
			centerX[i] = s.center.x;
			centerY[i] = s.center.y;
			centerZ[i] = s.center.z;
			sqRadius[i] = s.radius * s.radius;
			invRadius[i] = 1.0f / s.radius;
		}
	}

}


public struct Camera
...

```

之后就是复杂的射线和球碰撞计算了.用到了unsafe功能.

tMin就是判断射中的阀值

tMax是初始化射线用的距离(默认最大值)

先初始化射线的起始点和方向,循环次数,中心点半径等.

```C#

public struct SpheresSOA
{
	....

	public void Update(Sphere[] src)
	{
		...
	}

	public unsafe int HitSpheres(ref Ray r, float tMin, float tMax, ref Hit outHit)
	{
		float4 hitT = tMax;
		int4 id = -1;
		float4 rOriX = r.ori.x;
		float4 rOriY = r.ori.y;
		float4 rOriZ = r.ori.z;
		float4 rDirX = r.dir.x;
		float4 rDirY = r.dir.y;
		float4 rDirZ = r.dir.z;
		float4 tMin4 = tMin;
		int4 curId = new int4(0, 1, 2, 3);
		int simdLen = centerX.Length / 4;
		//获取一个float4指针
		float4* ptrCenterX = (float4*) centerX.GetUnsafeReadOnlyPtr();
		float4* ptrCenterY = (float4*) centerY.GetUnsafeReadOnlyPtr();
		float4* ptrCenterZ = (float4*) centerZ.GetUnsafeReadOnlyPtr();
		float4* ptrSqRadius = (float4*) sqRadius.GetUnsafeReadOnlyPtr();
		//TODO:
	}
}

```

射线点和圆心点的距离是A,它的平方即(len(P圆-P线))^2 => dot(P圆-P线,P圆-P线) => A^2. 因为方向是法向量,所以B线段的距离平方也可以描述为(dot(P圆-P线,Dir线))^2 => B^2. 那么C^2 = A^2-B^2 , 然后在拿C^2 和 半径平方D^2进行比较 , 如果 D^2 - C^2 == 0 则交点只有一个 刚相交(我们这里不算碰撞成功). <0 则无交点,不相交. >0 两个交点,碰撞成功. 因为D=E都是半径 , 所以可以求得F. 两个碰撞点到射线点的距离分别为B+F和B-F. 和保存的最短距离的进行比较,选出最短的距离. 然后再储存球的id和距离. 依次循环

![CPURayTrace_8](Images/CPURayTrace_8.png)

注意一些球可能是为了凑齐数据4个一组格式而不存在的数据,所以需要sCenterX < float.MaxValue 来做mask跳过

这时候储存的是4个float距离,还需要在之后进一步选出4个中的最小一个.


```C#
...

float4* ptrSqRadius = (float4*) sqRadius.GetUnsafeReadOnlyPtr();
for (int i = 0; i < simdLen; ++i)
{
	float4 sCenterX = *ptrCenterX;
	float4 sCenterY = *ptrCenterY;
	float4 sCenterZ = *ptrCenterZ;
	float4 sSqRadius = *ptrSqRadius;
	float4 coX = sCenterX - rOriX;
	float4 coY = sCenterY - rOriY;
	float4 coZ = sCenterZ - rOriZ;
	float4 nb = coX * rDirX + coY * rDirY + coZ * rDirZ;
	float4 c = coX * coX + coY * coY + coZ * coZ - sSqRadius;
	float4 discr = nb * nb - c;
	bool4 discrPos = discr > 0.0f; //如果有一个交点,,不算碰撞成功
	//if ray hits any of the 4 spheres
	if (any(discrPos))
	{
		float4 discrSq = sqrt(discr);

		//rau could hit spheres at t0&t1
		float4 t0 = nb - discrSq;
		float4 t1 = nb + discrSq;

		// if t0 is above min, take it (since it's the earlier hit); else try t1.
		//如果t0>tmin4 那就试一试t1  如果t1还不行  mask也是失败
		float4 t = select(t1, t0, t0 > tMin4);
		bool4 mask = discrPos & (t > tMin4) & (t < hitT) & (sCenterX < float.MaxValue);
		//if hit ,take it
		id = select(id, curId, mask);
		hitT = select(hitT, t, mask);
	}

	curId += int4(4);
	ptrCenterX++;
	ptrCenterY++;
	ptrCenterZ++;
	ptrSqRadius++;
}

```

之后就是从float4中找出最短的距离t,然后返回物体id和碰撞信息.

碰撞点 = 射线点 + dir*t

法线 = (碰撞点 - 圆心) / r    (/r是为了归一化)

最短距离 = t

如果什么都没有找到 则返回-1

```C#
...

for (int i = 0; i < simdLen; ++i)
{
	...
}

// now we have up to 4 hits, find and return closest one
float2 minT2 = min(hitT.xy, hitT.zw);
float minT = min(minT2.x, minT2.y);
if (minT < tMax)
{
	int laneMask = csum(int4(hitT == float4(minT)) * int4(1, 2, 4, 8));
	//get index of first closet lane
	//tzcnt:返回二进制 末尾零的个数
	int lane = tzcnt(laneMask);
	// if (lane < 0 || lane > 3) Debug.LogError($"invalid lane {lane}");
	int hitId = id[lane];
	//if (hitId < 0 || hitId >= centerX.Length) Debug.LogError($"invalid hitID {hitId}");
	float finalHitT = hitT[lane];
	outHit.pos = r.PointAt(finalHitT);
	outHit.normal = (outHit.pos - float3(centerX[hitId], centerY[hitId], centerZ[hitId])) *
					invRadius[hitId];
	outHit.t = finalHitT;
	return hitId;
}

return -1;

```

-----------------

## **4. 材质**

&emsp;&emsp; 每个球都会有自己的材质属性,所以要创建材质结构体用来储存属性.

创建一个C# **CPURayTracing.cs**,在上面添加一个结构体**Material**

这里把材质分为简单的三类:光线不反射的**Lambert**,光线镜面反射的**Metal**,光线穿过内部在内部发生折射的**Dielectric**,这三类的计算方式不同,所以用枚举**Type**加以区分.
  + guid:后面需要判断是否是自身,从而跳过用.C++可以不用这一属性,C#为了避免拷贝的地址不同,所以用guid来避免.
  + type:材质球属性
  + albedo:表面颜色
  + emissive:自发光颜色
  + roughness:粗糙度,反射用
  + ri:折射系数,内部折射用

![CPURayTrace_9](Images/CPURayTrace_9.jpg)

```C#
public struct Material
{
	public enum Type
	{
		Lambert,
		Metal,
		Dielectric
	}

	private static int GuidSpawn;

	public int guid;
	public Type type;
	public float3 albedo;
	public float3 emissive;
	public float roughness;
	public float ri;

	public Material(Type t, float3 a, float3 e, float r, float i)
		=> (guid, type, albedo, emissive, roughness, ri) = (GuidSpawn++, t, a, e, r, i);

	public bool HasEmission => emissive.x > 0 || emissive.y > 0 || emissive.z > 0;
}

public class CPURayTracing
{
}
```

因为材质球有自发光属性,是光照计算需要的数据.所以记录全部的自发光球体.返回**CPURayTracingMathUtil.cs**的**struct SpheresSOA**添加一点自发光数据的代码.

```C#
public struct SpheresSOA
{	
	...
	[ReadOnly] public NativeArray<float> invRadius;
	[ReadOnly] public NativeArray<int> emissives;
	public int emissiveCount;

	public SpheresSOA(int len)
	{
		...
		for (int i = len; i < simdLen; ++i)
		{
			...
		}
		emissives = new NativeArray<int>(simdLen, Allocator.Persistent);
		emissiveCount = 0;
	}

	public void Dispose()
	{
		...
		emissives.Dispose();
	}

	public void Update(Sphere[] src, Material[] mat)
	{
		emissiveCount = 0;
		for (var i = 0; i < src.Length; i++)
		{
			...
			if (mat[i].HasEmission)
			{
				emissives[emissiveCount++] = i;
			}
		}
	}

	...
}
```

-----------------

## **5. 数据准备**

&emsp;&emsp; 上面我们基本把工具都做的差不多了,在渲染之前还要做一点点(亿点点)数据准备.

在**CPURayTracing.cs**中导入一堆namespace和static namespace.

```C#
using Unity.Burst;
using Unity.Collections;
using Unity.Jobs;
using Unity.Mathematics;
using UnityEngine;
using static Unity.Mathematics.math;
using static MyGraphics.Scripts.CPURayTracing.CPURayTracingMathUtil;

public struct Material
{
	...
}

public class CPURayTracing
{
	...
}
```

然后自己规定一点数据.比如说:
  + DO_SAMPLES_PER_PIXEL:一个像素要发射多少射线
  + kMinT:判断射中的阈值
  + tMaxT:初始化射线的最大值
  + kMaxDepth:光线深度循环最大的次数.光线碰到物体会进行一次新的弹射,然后再碰到物体,再次弹射,循环ing.所以可能会出现一束光反复弹来弹去,很难终止.次数一旦上去会对性能造成很大的压力,当然次数给少了渲染效果也不好看.

```C#
public class CPURayTracing
{
	private const int DO_SAMPLES_PER_PIXEL = 4;

	private const float kMinT = 0.001f;
	private const float kMaxT = float.MaxValue; //1.0e7f;
	private const int kMaxDepth = 10;
}
```

再准备要渲染的球的数据和材质数据,关系是一对一的.可以利用**define**对数据做区分,用**region**让代码看起来干净.

先在顶部定义#define DO_BIG_SCENE, 然后在下面写两个属性**static Sphere[] spheresData**和**static Material[] sphereMatsData**用来储存球和材质球,别忘了用region包起来.

```C#

#define DO_BIG_SCENE

using Unity.Burst;
....

public class CPURayTracing
{
	...
	private const int kMaxDepth = 10;

	#region Data
	private static Sphere[] spheresData =
	{
		//TODO:Data
	}

	private static Material[] sphereMatsData =
	{
		//TODO:Data
	}
	#endregion
}

```

之后就是把数据丢进去,数据可以随便写...只要数量一致的就好了.

```C#

		private static Sphere[] spheresData =
		{
			new Sphere(new float3(0, -100.5f, -1), 100),
			new Sphere(new float3(2, 0, -1), 0.5f),
			new Sphere(new float3(0, 0, -1), 0.5f),
			new Sphere(new float3(-2, 0, -1), 0.5f),
			new Sphere(new float3(2, 0, 1), 0.5f),
			new Sphere(new float3(0, 0, 1), 0.5f),
			new Sphere(new float3(-2, 0, 1), 0.5f),
			new Sphere(new float3(0.5f, 1, 0.5f), 0.5f),
			new Sphere(new float3(-1.5f, 1.5f, 0f), 0.3f),
#if DO_BIG_SCENE
			new Sphere(new float3(4, 0, -3), 0.5f),
			new Sphere(new float3(3, 0, -3), 0.5f),
			new Sphere(new float3(2, 0, -3), 0.5f),
			new Sphere(new float3(1, 0, -3), 0.5f),
			new Sphere(new float3(0, 0, -3), 0.5f),
			new Sphere(new float3(-1, 0, -3), 0.5f),
			new Sphere(new float3(-2, 0, -3), 0.5f),
			new Sphere(new float3(-3, 0, -3), 0.5f),
			new Sphere(new float3(-4, 0, -3), 0.5f),
			new Sphere(new float3(4, 0, -4), 0.5f),
			new Sphere(new float3(3, 0, -4), 0.5f),
			new Sphere(new float3(2, 0, -4), 0.5f),
			new Sphere(new float3(1, 0, -4), 0.5f),
			new Sphere(new float3(0, 0, -4), 0.5f),
			new Sphere(new float3(-1, 0, -4), 0.5f),
			new Sphere(new float3(-2, 0, -4), 0.5f),
			new Sphere(new float3(-3, 0, -4), 0.5f),
			new Sphere(new float3(-4, 0, -4), 0.5f),
			new Sphere(new float3(4, 0, -5), 0.5f),
			new Sphere(new float3(3, 0, -5), 0.5f),
			new Sphere(new float3(2, 0, -5), 0.5f),
			new Sphere(new float3(1, 0, -5), 0.5f),
			new Sphere(new float3(0, 0, -5), 0.5f),
			new Sphere(new float3(-1, 0, -5), 0.5f),
			new Sphere(new float3(-2, 0, -5), 0.5f),
			new Sphere(new float3(-3, 0, -5), 0.5f),
			new Sphere(new float3(-4, 0, -5), 0.5f),
			new Sphere(new float3(4, 0, -6), 0.5f),
			new Sphere(new float3(3, 0, -6), 0.5f),
			new Sphere(new float3(2, 0, -6), 0.5f),
			new Sphere(new float3(1, 0, -6), 0.5f),
			new Sphere(new float3(0, 0, -6), 0.5f),
			new Sphere(new float3(-1, 0, -6), 0.5f),
			new Sphere(new float3(-2, 0, -6), 0.5f),
			new Sphere(new float3(-3, 0, -6), 0.5f),
			new Sphere(new float3(-4, 0, -6), 0.5f),
			new Sphere(new float3(1.5f, 1.5f, -2), 0.3f),
#endif // #if DO_BIG_SCENE
		};

		private static Material[] sphereMatsData =
		{
			new Material(Material.Type.Lambert, new float3(0.8f, 0.8f, 0.8f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Lambert, new float3(0.8f, 0.4f, 0.4f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Lambert, new float3(0.4f, 0.8f, 0.4f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Metal, new float3(0.4f, 0.4f, 0.8f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Metal, new float3(0.4f, 0.8f, 0.4f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Metal, new float3(0.4f, 0.8f, 0.4f), new float3(0, 0, 0), 0.2f, 0),
			new Material(Material.Type.Metal, new float3(0.4f, 0.8f, 0.4f), new float3(0, 0, 0), 0.6f, 0),
			new Material(Material.Type.Dielectric, new float3(0.4f, 0.4f, 0.4f), new float3(0, 0, 0), 0, 1.5f),
			new Material(Material.Type.Lambert, new float3(0.8f, 0.6f, 0.2f), new float3(30, 25, 15), 0, 0),
#if DO_BIG_SCENE
			new Material(Material.Type.Lambert, new float3(0.1f, 0.1f, 0.1f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Lambert, new float3(0.2f, 0.2f, 0.2f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Lambert, new float3(0.3f, 0.3f, 0.3f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Lambert, new float3(0.4f, 0.4f, 0.4f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Lambert, new float3(0.5f, 0.5f, 0.5f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Lambert, new float3(0.6f, 0.6f, 0.6f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Lambert, new float3(0.7f, 0.7f, 0.7f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Lambert, new float3(0.8f, 0.8f, 0.8f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Lambert, new float3(0.9f, 0.9f, 0.9f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Metal, new float3(0.1f, 0.1f, 0.1f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Metal, new float3(0.2f, 0.2f, 0.2f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Metal, new float3(0.3f, 0.3f, 0.3f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Metal, new float3(0.4f, 0.4f, 0.4f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Metal, new float3(0.5f, 0.5f, 0.5f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Metal, new float3(0.6f, 0.6f, 0.6f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Metal, new float3(0.7f, 0.7f, 0.7f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Metal, new float3(0.8f, 0.8f, 0.8f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Metal, new float3(0.9f, 0.9f, 0.9f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Metal, new float3(0.8f, 0.1f, 0.1f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Metal, new float3(0.8f, 0.5f, 0.1f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Metal, new float3(0.8f, 0.8f, 0.1f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Metal, new float3(0.4f, 0.8f, 0.1f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Metal, new float3(0.1f, 0.8f, 0.1f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Metal, new float3(0.1f, 0.8f, 0.5f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Metal, new float3(0.1f, 0.8f, 0.8f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Metal, new float3(0.1f, 0.1f, 0.8f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Metal, new float3(0.5f, 0.1f, 0.8f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Lambert, new float3(0.8f, 0.1f, 0.1f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Lambert, new float3(0.8f, 0.5f, 0.1f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Lambert, new float3(0.8f, 0.8f, 0.1f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Lambert, new float3(0.4f, 0.8f, 0.1f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Lambert, new float3(0.1f, 0.8f, 0.1f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Lambert, new float3(0.1f, 0.8f, 0.5f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Lambert, new float3(0.1f, 0.8f, 0.8f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Lambert, new float3(0.1f, 0.1f, 0.8f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Metal, new float3(0.5f, 0.1f, 0.8f), new float3(0, 0, 0), 0, 0),
			new Material(Material.Type.Lambert, new float3(0.1f, 0.2f, 0.5f), new float3(3, 10, 20), 0, 0),
#endif
		};

```

然后还要创建之前写的球交数据结构体**SpheresSOA**,别忘了销毁.

```C#
public class CPURayTracing
{
	#region Data
	...
	#endregion
	
	private SpheresSOA spheresSOA;

	public CPURayTracing()
	{
		spheresSOA = new SpheresSOA(spheresData.Length);
	}

	public void Dispose()
	{
		spheresSOA.Dispose();
	}
}

```

当然还要创建相机,不然连拍什么都不知道...

创建一个**DoDraw**方法,用于渲染绘制的.

如果我们要拍大场景,光圈建议小一点,模糊不会那么严重.

同时我们这里也把球和材质的更新也写到这里.

```C#
public class CPURayTracing
{

	public void Dispose()
	{
		...
	}

	public void DoDraw(int screenWidth, int screenHeight)
	{
		float3 lookFrom = new float3(0, 2, 3);
		float3 lookAt = new float3(0, 0, 0);
		float distToFocus = 3f;
		float aperture = 0.1f;
#if DO_BIG_SCENE
		aperture *= 0.2f;
#endif
		Camera cam = new Camera(lookFrom, lookAt, new float3(0, 1, 0), 60,
			(float) screenWidth / (float) screenHeight, aperture, distToFocus);
		
		spheresSOA.Update(spheresData, sphereMatsData);

	}
}
```

-----------------

## **6. 射线**

&emsp;&emsp; 屏幕是由像素组成的.那么我们可以由遍历像素,让它发出N(DO_SAMPLES_PER_PIXEL)根射线计算光照求结果.这样就能得到最后效果了.

这里我们用Job来遍历height,然后再在Job里面嵌套一个for width,从而实现遍历全部的像素.

在**CPURayTracing.cs**中创建Job **TraceRowJob**

```C#
public class CPURayTracing
{
	...

	public void Dispose()
	{
		...
	}

	[BurstCompile]
	private struct TraceRowJob : IJobParallelFor
	{
		public void Execute(int y)
		{
		}
	}

	public void DoDraw(int screenWidth, int screenHeight)
	{
		...
	}
}
```

给**TraceRowJob**添加基础的属性
  + screenWidth/screenHeight:屏幕尺寸
  + frameCount:主要做颜色lerp和随机种子用
  + cam:摄像机属性
  + backbuffer:颜色数据
  + rayCounter:射线统计
  + spheres:球的信息
  + materials:材质信息

```C#

private struct TraceRowJob : IJobParallelFor
{
	public int screenWidth, screenHeight, frameCount;
	public Camera cam;

	[NativeDisableParallelForRestriction] public NativeArray<Color> backbuffer;
	[NativeDisableParallelForRestriction] public NativeArray<int> rayCounter;
	[NativeDisableParallelForRestriction] public SpheresSOA spheres;
	[NativeDisableParallelForRestriction] public NativeArray<Material> materials;

	public void Execute(int y)
	{
	}
}

```

修改**DoDraw(int screenWidth, int screenHeight)**方法 , 在里面创建Job并且完成数据的配置. Job要执行的长度即**screenHeight**

```C#
public class CPURayTracing
{
	[BurstCompile]
	private struct TraceRowJob : IJobParallelFor
	{
		...
	}

	public void DoDraw(float time, int frameCount, int screenWidth, int screenHeight,
		NativeArray<Color> backbuffer, out int outRayCount)
	{
		int rayCount = 0;

		float3 lookFrom = new float3(0, 2, 3);
		...
		spheresSOA.Update(spheresData, sphereMatsData);
			
		TraceRowJob job;
		job.screenWidth = screenWidth;
		job.screenHeight = screenHeight;
		job.frameCount = frameCount;
		job.backbuffer = backbuffer;
		job.cam = cam;
		job.rayCounter = new NativeArray<int>(1, Allocator.TempJob);
		job.spheres = spheresSOA;
		job.materials = new NativeArray<Material>(sphereMatsData, Allocator.TempJob);

		var fence = job.Schedule(screenHeight, 4);
		fence.Complete();

		rayCount = job.rayCounter[0];
		job.rayCounter.Dispose();
		job.materials.Dispose();
		
		outRayCount = rayCount;
	}
}

```

返回Job继续编写.

为了达到遍历像素数量,所以Job里面要For screenWidth.然后每个像素还要发出N(DO_SAMPLES_PER_PIXEL)根射线,所以还要For一次.

```C#
private struct TraceRowJob : IJobParallelFor
{
	...

	public void Execute(int y)
	{
		for (int x = 0; x < screenWidth; ++x)
		{
			for (int s = 0; s < DO_SAMPLES_PER_PIXEL; s++)
			{
				//TODO:发射射线
			}
		}
	}
}

```

因为像素不是一个点,也是有大小的.为了让结果更接近真实准确,可以在像素的大小内随机分布射线去发射,而不是只在像素的中心点发射.

初始化随机种子(随便写,开心就好),创建射线.

```C#

	public void Execute(int y)
	{
		float invWidth = 1.0f / screenWidth;
		float invHeight = 1.0f / screenHeight;

		uint state = (uint) (y * 9781 + frameCount * 6271) | 1;


		for (int x = 0; x < screenWidth; ++x)
		{
			for (int s = 0; s < DO_SAMPLES_PER_PIXEL; s++)
			{
				float u = (x + RandomFloat01(ref state)) * invWidth;
				float v = (y + RandomFloat01(ref state)) * invHeight;
				Ray r = cam.GetRay(u, v, ref state);

				//TODO:光照采样
			}
		}
	}

```

有了射线之后就可以利用之前写的**SpheresSOA**和**Material**进行光线追踪了.

在**CPURayTracing.cs**中创建**HitWorld**用于判断光线是否碰撞成功

```C#
	public class CPURayTracing
	{
		public void Dispose()
		{
			...
		}

		private static bool HitWorld(Ray r, float tMin, float tMax
			, ref Hit outHit, ref int outID, ref SpheresSOA spheres)
		{
			outID = spheres.HitSpheres(ref r, tMin, tMax, ref outHit);
			return outID != -1;
		}

		[BurstCompile]
		private struct TraceRowJob : IJobParallelFor
		{
			....
		}

		...
	}
```

-----------------

## **7. 基础颜色**

&emsp;&emsp; 老乡别跑,终于开始讲渲染了.

创建一个方法**Trace**,主要用于得到最终的颜色.

```C#
private static bool HitWorld(Ray r, float tMin, float tMax
	, ref Hit outHit, ref int outID, ref SpheresSOA spheres)
{
	...
}

private static float3 Trace(Ray r, int depth, ref int inoutRayCount, ref SpheresSOA spheres,
	NativeArray<Material> materials, ref uint randState, bool doMaterialE = true)
{
	//TODO:
}

[BurstCompile]
private struct TraceRowJob : IJobParallelFor
{
	....
}
```

然后完善**Trace**方法.**Scatter**方法讲在后面讲到,主要用于得到颜色和和决定射线继续怎么走.
  + inoutRayCount,每产生一根射线就累加一次,用于信息统计
  + doMaterialE,走自发光还是光照详细计算,后面还会在补充
  + kMaxDepth,光线弹射的最大次数,避免弹射过多,造成性能紧张.而且如果albedo<1越到后面的弹射造成的颜色几乎衰减为0

kMaxDepth:比如我们假设albedo(吸收率)为0.5,然后需要把光线经过的全部颜色递归累加起来(简单demo不考虑光线弹射一次会散开多根).可以发现随着弹射,系数变小,后面产生的颜色已经影响很小了.而可能出现反复弹射,那么天河二号来了也会死循环.

![CPURayTrace_22](Images/CPURayTrace_22.png)

![CPURayTrace_23](Images/CPURayTrace_23.jpg)

这里的最终颜色的公式比较简单.

color = 自发光 + 灯光产生的颜色 + 吸收率(albedo) * 继续弹射的颜色.

albedo:可以直白理解越黑色越吸收光.比如吸光材料/布是黑色的.

如果弹射过多(depth < kMaxDepth),则直接返回自发光.

如果没有射中,返回天空颜色.

```C#

private static float3 Trace(Ray r, int depth, ref int inoutRayCount, ref SpheresSOA spheres,
			NativeArray<Material> materials, ref uint randState, bool doMaterialE = true)
{
	Hit rec = default;
	int id = 0;
	++inoutRayCount;
	if (HitWorld(r, kMinT, kMaxT, ref rec, ref id, ref spheres))
	{
		var mat = materials[id];
		var matE = mat.emissive;
		if (depth < kMaxDepth && Scatter(mat, r, rec, out float3 attenuation, out Ray scattered,
			out float3 lightE, ref inoutRayCount, ref spheres, materials, ref randState))
		{
			if (all(attenuation == 0))
			{
				return matE + lightE;
			}
			else
			{
				return matE + lightE + attenuation * Trace(scattered, depth + 1, ref inoutRayCount, ref spheres,
					materials, ref randState, doMaterialE);
			}
		}
		else
		{
			return matE;
		}
	}
	else
	{
		// sky
		float3 unitDir = r.dir;
		float t = 0.5f * (unitDir.y + 1.0f);
		return ((1.0f - t) * new float3(1.0f, 1.0f, 1.0f) + t * new float3(0.5f, 0.7f, 1.0f)) * 0.3f;
	}
}

```

然后编写**Scatter**方法.**outLightE**后面写光照计算用.

```C#

public class CPURayTracing
{
	private static bool HitWorld(Ray r, float tMin, float tMax
	, ref Hit outHit, ref int outID, ref SpheresSOA spheres)
	{
		...
	}

	private static bool Scatter(Material mat, Ray r_in, Hit rec, out float3 attenuation, out Ray scattered,
		out float3 outLightE, ref int inoutRayCount, ref SpheresSOA spheres, NativeArray<Material> materials,
		ref uint randState)
	{
		//TODO:
	}


	private static float3 Trace(Ray r, int depth, ref int inoutRayCount, ref SpheresSOA spheres,
		NativeArray<Material> materials, ref uint randState, bool doMaterialE = true)
	{
		...
	}
}

```

先计算**Material.Type.Lambert**,同时把光照计算先去掉.

光线进来,在碰撞点,随机选择一个向外的方向再次反弹出去.本来可能反弹很多很多条的,但是计算量非常大.这里只随机选择一条.

![CPURayTrace_24](Images/CPURayTrace_24.jpg)

```C#
private static bool Scatter(Material mat, Ray r_in, Hit rec, out float3 attenuation, out Ray scattered,
	out float3 outLightE, ref int inoutRayCount, ref SpheresSOA spheres, NativeArray<Material> materials,
	ref uint randState)
{
	outLightE = new float3(0, 0, 0);
	if (mat.type == Material.Type.Lambert)
	{
		//随机在表面一个点发散
		float3 target = rec.pos + rec.normal + RandomUnitVector(ref randState);
		scattered = new Ray(rec.pos, normalize(target - rec.pos));
		attenuation = mat.albedo;

		//TODO:光照

		return true;
	}
	else if (mat.type == Material.Type.Metal)
	{
		//TODO:
	}
	else if (mat.type == Material.Type.Dielectric)
	{
		//TODO:
	}
	else
	{
		//TODO:BUG标记
	}

	return false;
}
```

然后就是**Material.Type.Metal**.类似于镜面反射,可以之用**reflect**方法搞定.然后这里存在rougness,即不是光滑的平面.所以反射可能不会那么规则,那么加一点随机偏移既可.但是也有可能会偏移到平面内部,直接不发生反射,所以需要做检测.

![CPURayTrace_25](Images/CPURayTrace_25.jpg)

```C#

if (mat.type == Material.Type.Lambert)
{
	...
}
else if (mat.type == Material.Type.Metal)
{
	float3 refl = reflect(r_in.dir, rec.normal);
	scattered = new Ray(rec.pos, normalize(refl + mat.roughness * RandomInUnitSphere(ref randState)));
	attenuation = mat.albedo;
	return dot(scattered.dir, rec.normal) > 0;
}
...

```

然后就是**Material.Type.Dielectric**.类似于折射.光线要折射进球内部再折射出去.所以在此之前要先写两个数学方法.

在**CPURayTracingMathUtil.cs**中补充两个方法
  + **Refract**,折射
  + **Schlick**,Schlick Fresnel
  + 详细可以参考这篇: https://graphics.stanford.edu/courses/cs148-10-summer/docs/2006--degreve--reflection_refraction.pdf

```C#
public static class CPURayTracingMathUtil
{
	//Math
	//https://graphics.stanford.edu/courses/cs148-10-summer/docs/2006--degreve--reflection_refraction.pdf
	//----------------------------

	public static bool Refract(float3 v, float3 n, float nint, out float3 outRefracted)
	{
		float dt = dot(v, n);
		float discr = 1.0f - nint * nint * (1 - dt * dt);
		if (discr > 0)
		{
			outRefracted = nint * (v - n * dt) - n * sqrt(discr);
			return true;
		}

		outRefracted = new float3(0, 0, 0);
		return false;
	}

	// cosine越大  reflProb越小    ri越大  reflProb越大
	public static float Schlick(float cosine, float ri)
	{
		float r0 = (1 - ri) / (1 + ri);
		r0 = r0 * r0;
		return r0 + (1 - r0) * pow(1 - cosine, 5);
	}

	//Random
	//-------------------

	//生成随机数
	private static uint XorShift32(ref uint state)
	{
		...
	}
	...
}
```

返回继续写**Material.Type.Dielectric**.如果折射失败,或者是靠近边缘的菲涅尔,则可能发生反射.

![CPURayTrace_26](Images/CPURayTrace_26.jpg)

```C#

else if (mat.type == Material.Type.Metal)
{
	...
}
else if (mat.type == Material.Type.Dielectric)
{
	float3 outWN; //out world normal
	float3 rdir = r_in.dir;
	float nint;
	attenuation = new float3(1, 1, 1);
	float3 refr;
	float reflProb;
	float cosine;
	float dn = dot(rdir, rec.normal);
	//折射的  射入和射出
	if (dn > 0)
	{
		outWN = -rec.normal;
		nint = mat.ri;
		cosine = mat.ri * dn;
	}
	else
	{
		outWN = rec.normal;
		nint = 1.0f / mat.ri;
		cosine = -dn;
	}
	
	//如果折射射入成功  计算光滑度
	//reflProb越大则越粗糙    走反射概率越大
	//cosine越大  reflProb越小    ri越大  reflProb越大
	if (Refract(rdir, outWN, nint, out refr))
	{
		reflProb = Schlick(cosine, mat.ri);
	}
	else
	{
		reflProb = 1;
	}

	//越光滑  
	if (RandomFloat01(ref randState) < reflProb)
	{
		float3 refl = reflect(rdir, rec.normal);
		scattered = new Ray(rec.pos, normalize(refl));
	}
	else
	{
		scattered = new Ray(rec.pos, normalize(refr));
	}

	return true;
}
else
{
	...
}

```

最后就是BUG标记.避免意外情况

```C#
...
else if (mat.type == Material.Type.Dielectric)
{
	...
}
else
{
	//Bug标记
	attenuation = new float3(1, 0, 1);
	scattered = default;
	return false;
}
return false;
```

这样一份简单的着色基本写完了.接着可以完善一下代码看看效果.

-----------------

## **8. 基础效果**

&emsp;&emsp; 完善**TraceRowJob**的**Execute(int y)**.利用**Trace**得到颜色再除权.之后再和之前的颜色做lerp,以便得到少噪点和错误的颜色.

finalColor = lerp(nowColor,oldColor,frameCount/(frameCount+1))

![CPURayTrace_32](Images/CPURayTrace_32.jpg)

```C#

private struct TraceRowJob : IJobParallelFor
{
	...

	public void Execute(int y)
	{
		int backbufferIdx = y * screenWidth;
		float invWidth = 1.0f / screenWidth;
		float invHeight = 1.0f / screenHeight;
		float lerpFac = ((float) frameCount / (frameCount + 1));
		uint state = (uint) (y * 9781 + frameCount * 6271) | 1;
		int rayCount = 0;
		for (int x = 0; x < screenWidth; ++x)
		{
			float3 col = new float3(0, 0, 0);
			for (int s = 0; s < DO_SAMPLES_PER_PIXEL; s++)
			{
				float u = (x + RandomFloat01(ref state)) * invWidth;
				float v = (y + RandomFloat01(ref state)) * invHeight;
				Ray r = cam.GetRay(u, v, ref state);
				col += Trace(r, 0, ref rayCount, ref spheres, materials, ref state);
			}

			col /= (float) DO_SAMPLES_PER_PIXEL;

			Color prev = backbuffer[backbufferIdx];
			col = new float3(prev.r, prev.g, prev.b) * lerpFac + col * (1 - lerpFac);
			backbuffer[backbufferIdx] = new Color(col.x, col.y, col.z, 1);
			backbufferIdx++;
		}

		//TODO: how to do atomics add?
		rayCounter[0] += rayCount;
	}
}

```

返回**CPURayTracingTest.cs**.

创建**CPURayTracing rayTracing**,别忘记销毁.

创建**int frameCounter**,统计帧数,随机种子,也是finalColor的lerp用的参数.

```C#
public class CPURayTracingTest : MonoBehaviour
{
	...

	private NativeArray<Color> backBuffer;
	private CPURayTracing rayTracing;

	private int frameCounter;

	private void Start()
	{
		...

		uiImage.texture = backBufferTex;

		rayTracing = new CPURayTracing();
	}

	private void OnDestroy()
	{
		backBuffer.Dispose();
		rayTracing.Dispose();
	}
}

```

创建一个函数**UpdateLoop**,执行绘制.并且在**Update**中调用.

```C#
private void Update()
{
	UpdateLoop();

	backBufferTex.LoadRawTextureData(backBuffer);
	backBufferTex.Apply();
}
		
private void UpdateLoop()
{
	int rayCount;
	rayTracing.DoDraw(Time.timeSinceLevelLoad, frameCounter++, backBufferTex.width, backBufferTex.height,
		backBuffer, out rayCount);
}

```

运行,可以看到有很多的黑点/噪点.

![CPURayTrace_27](Images/CPURayTrace_27.jpg)

那是在一块区域上一些光线的反射弹到了自发光上面,而一些没有.所以会出现这种感觉(其实这种效果是错的,后面说).

把自发光去除,效果就正常很多.

![CPURayTrace_28](Images/CPURayTrace_28.jpg)

-----------------

## **9. 自发光**

&emsp;&emsp; 因为自发光的存在,所以**Material.Type.Lambert**还需要继续改造下.

为了方便观察自发光产生的效果,需要在**CPURayTracing*.cs** #define DO_LIGHT_SAMPLING 进行开关处理.

```C#
#define DO_LIGHT_SAMPLING
#define DO_BIG_SCENE

public struct Material
{
	...
}

public class CPURayTracing
{
	...
}

```

之前的问题我们已经了解到.噪点主要原因是随机的光线一些弹射在了自发光上面,一些没有.所以我们在**Trace**中可以单独对lambert的反射进行处理,让它计算最终颜色的时候不加自发光.把自发光的计算放到**Scatter**中处理.

```C#
private static float3 Trace(Ray r, int depth, ref int inoutRayCount, ref SpheresSOA spheres,
			NativeArray<Material> materials, ref uint randState, bool doMaterialE = true)
{
	...
	if (HitWorld(r, kMinT, kMaxT, ref rec, ref id, ref spheres))
	{
		...
		if (depth < kMaxDepth && Scatter(mat, r, rec, out float3 attenuation, out Ray scattered,
			out float3 lightE, ref inoutRayCount, ref spheres, materials, ref randState))
		{
#if DO_LIGHT_SAMPLING
			if (!doMaterialE)
			{
				matE = new float3(0, 0, 0);
			}

			doMaterialE = (mat.type != Material.Type.Lambert);
#endif
			if (all(attenuation == 0))
			{
				return matE + lightE;
			}
			else
			{
				return matE + lightE + attenuation * Trace(scattered, depth + 1, ref inoutRayCount, ref spheres,
					materials, ref randState, doMaterialE);
			}
		}
		else
		{
			return matE;
		}
	}
	else
	{
		...
	}
}
```

![CPURayTrace_29](Images/CPURayTrace_29.jpg)

可以看到噪点好像少了很多.但是这样就没有了自发光的计算,所以在**Scatter**完善它.

可以让每次碰撞,碰撞点都必定向自发光发射射线,判断这个点是否应该被光照亮,将产生什么颜色.

想想地球OL也是.射线到被红灯照亮的A球,A球泛红.再弹射到被绿灯照亮的B球,泛绿.再到被蓝灯(Doge)照亮的C球,泛蓝.那么最终颜色是1*红+0.5*绿+0.25*蓝.

而如果按照之前的写法就是,射线经过A球,到B球,再到C球,最后到蓝灯.颜色可能就只有蓝色了.

注意计算自发光的时候要跳过自己.

不过它这里这样计算好像会过亮...算了抄它...

```C#
private static bool Scatter(Material mat, Ray r_in, Hit rec, out float3 attenuation, out Ray scattered,
	out float3 outLightE, ref int inoutRayCount, ref SpheresSOA spheres, NativeArray<Material> materials,
	ref uint randState)
{
	outLightE = new float3(0, 0, 0);
	if (mat.type == Material.Type.Lambert)
	{
		//随机在表面一个点发散
		float3 target = rec.pos + rec.normal + RandomUnitVector(ref randState);
		scattered = new Ray(rec.pos, normalize(target - rec.pos));
		attenuation = mat.albedo;

#if DO_LIGHT_SAMPLING
		for (int j = 0; j < spheres.emissiveCount; ++j)
		{
			int i = spheres.emissives[j];
			//if mat is self then skip
			//if(&mat == &smat)
			//	continue;//skip self
			if (mat.guid == materials[i].guid)
			{
				continue;
			}

			//var s = spheres[i];
			float3 sCenter = new float3(spheres.centerX[i], spheres.centerY[i], spheres.centerZ[i]);
			float sqRadius = spheres.sqRadius[i];

			float sqLen = lengthsq(rec.pos - sCenter);

			if (sqLen == 0)
			{
				continue;
			}

			//create a random direction towards sphere
			//coord system for sampling: sw,su,sv
			float3 sw = normalize(sCenter - rec.pos);
			float3 su = normalize(cross(abs(sw.x) > 0.01f ? new float3(0, 1, 0) : new float3(1, 0, 0), sw));
			float3 sv = cross(sw, su);
			//sample sphere by solid anglePI
			//为了准确性   发光球的半径越小或者两球距离过大  射线越会朝向发光球
			//否则  发光球的半径越大或者两球距离过小  采样会分散一点 射线越会偏离发光球
			float cosAMax = sqrt(max(0.0f, 1.0f - sqRadius / sqLen));
			float eps1 = RandomFloat01(ref randState);
			float eps2 = RandomFloat01(ref randState);
			float cosA = 1 - eps1 * (1 - cosAMax);
			float sinA = sqrt(1.0f - cosA * cosA);
			float phi = 2 * PI * eps2;
			// 碰撞点朝向自发光球 做 随机半球偏离  
			float3 l = su * cos(phi) * sinA + sv * sin(phi) * sinA + sw * cosA;
			l = normalize(l);

			//shoot shadow ray
			Hit lightHit = default(Hit);
			int hitID = 0;
			inoutRayCount++;
			if (HitWorld(new Ray(rec.pos, l), kMinT, kMaxT, ref lightHit, ref hitID, ref spheres) && hitID == i)
			{
				//TODO:是否存在能量不守恒
				//如  E * 2*kPI*(1-0)/kPI => E*2  超出范围了
				//如  E * 2*kPI*(1-0.5)/kPI => E  一半角度的时候 已经满能量了
				float omega = 2 * PI * (1 - cosAMax);

				float3 rdir = r_in.dir;
				float3 nl = dot(rec.normal, rdir) < 0.0f ? rec.normal : -rec.normal;
				outLightE += (mat.albedo * materials[i].emissive) * (max(0.0f, dot(l, nl)) * omega / PI);
			}
		}
#endif
		return true;
	}
	...
}
```

这样自发光的光照就做好了.我用完了是这个样子,你们用完了也是这个样子.

![CPURayTrace_31](Images/CPURayTrace_31.jpg)

![CPURayTrace_30](Images/CPURayTrace_30.jpg)


-----------------

## **10. 其它**

&emsp;&emsp; 他这里还有一点点别的模块**动画**,**主线程**,**性能显示**.

### **10.1 动画**

&emsp;&emsp; 先说动画吧.其实就是让两个球动起来.

在**CPURayTracing.cs**中 #define DO_ANIMATE 方便开关和观察. 还有 **float DO_ANIMATE_SMOOTHING** 因为是动态的,所以lerpColor到后面的权重不能接近于1. 然后球就是根据输入的时间进行sin或cos运动就好了.

```C#
#define DO_ANIMATE 
#define DO_LIGHT_SAMPLING

...

public class CPURayTracing
{
	private const int DO_SAMPLES_PER_PIXEL = 4;
	private const float DO_ANIMATE_SMOOTHING = 0.5f;
	...

	[BurstCompile]
	private struct TraceRowJob : IJobParallelFor
	{
		...

		public void Execute(int y)
		{
			...
			float lerpFac = ((float) frameCount / (frameCount + 1));
#if DO_ANIMATE
			lerpFac = lerpFac * DO_ANIMATE_SMOOTHING;//saturate(lerpFac * DO_ANIMATE_SMOOTHING);
#endif
			...
		}
	}

	public void DoDraw(float time, int frameCount, int screenWidth, int screenHeight,
			NativeArray<Color> backbuffer, out int outRayCount)
	{
		int rayCount = 0;
#if DO_ANIMATE
		spheresData[1].center.y = cos(time) + 1.0f;
		spheresData[8].center.z = sin(time) * 0.3f;
#endif
		...
	}
}

```

![CPURayTrace_33](Images/CPURayTrace_33.jpg)

可以看到残影和很明显的噪点,建议关闭23333.注释掉#define DO_ANIMATE就好了

```C#

// #define DO_ANIMATE
#define DO_LIGHT_SAMPLING
...

```

### **10.2 主线程**

&emsp;&emsp; 就是不用Job直接走主线程.会严重卡死强烈建议别这么做.毕竟我们不是做某剑六

在**CPURayTracing.cs**中 #define DO_THREADED 方便开关和观察. 如果开启则走多线程的Job,否则走主线程. Job可以直接用for循环来Execute,所以改造比较简单.

```C#
// #define DO_ANIMATE
#define DO_LIGHT_SAMPLING
#define DO_THREADED
...


public class CPURayTracing
{
	...

	public void DoDraw(float time, int frameCount, int screenWidth, int screenHeight,
		NativeArray<Color> backbuffer, out int outRayCount)
	{
		...
		job.materials = new NativeArray<Material>(sphereMatsData, Allocator.TempJob);

#if DO_THREADED
		var fence = job.Schedule(screenHeight, 4);
		fence.Complete();
#else
		for (int y = 0; y < screenHeight; ++y)
		{
			job.Execute(y);
		}
#endif
	}
}

```

### **10.3 性能现实**

&emsp;&emsp; 把性能现实到屏幕上,方便观察.

创建一个**UI.Text**,如下图设置.

![CPURayTrace_34](Images/CPURayTrace_34.jpg)

在**CPURayTracingTest.cs**中添加组件代码,并且在外面绑定刚添加的创建的**UI Text**.

```C#

public class CPURayTracingTest : MonoBehaviour
{
	...

	public Text uiPrefText;
	public RawImage uiImage;

	...
}

```

![CPURayTrace_35](Images/CPURayTrace_35.jpg)

继续返回**CPURayTracingTest.cs**,完成性能统计. 用**Stopwatch**做耗时统计. 因为存在随机,每隔N帧统计一次平均值即可,不然会跳来跳去. 射线总数量我们之前也已经统计好了.

```C#

public class CPURayTracingTest : MonoBehaviour
{
	...

	private Stopwatch stopWatch;
	private int updateCounter;
	private int frameCounter;
	private long rayCounter;

	private void Start()
	{
		...

		rayTracing = new CPURayTracing();
		stopWatch = new Stopwatch();
	}

	private void Update()
	{
		UpdateLoop();
		if (updateCounter == 10)
		{
			var s = (float) ((double) stopWatch.ElapsedTicks / Stopwatch.Frequency) / updateCounter;
			var ms = s * 1000.0f;
			//1.0e-6f 百万
			var mrayS = (float) rayCounter / updateCounter / s * 1.0e-6f;
			var mrayFr = (float) rayCounter / updateCounter * 1.0e-6f;
			uiPrefText.text =
				$"{ms:F2}ms ({1.0f / s:F2}FPS) {mrayS:F2}Mrays/s {mrayFr:F2}Mrays/frame {frameCounter} frames";
			updateCounter = 0;
			rayCounter = 0;
			stopWatch.Reset();
		}

		...
	}

	private void UpdateLoop()
	{
		stopWatch.Start();
		int rayCount;
		rayTracing.DoDraw(Time.timeSinceLevelLoad, frameCounter++, backBufferTex.width, backBufferTex.height,
			backBuffer, out rayCount);
		stopWatch.Stop();
		updateCounter++;
		rayCounter += rayCount;
	}
}

```

到此完结散花!!!

有兴趣也可以去看看这两个效果.第一个简单很多也符合这篇,第二个就有很多数学相关的.

https://www.shadertoy.com/view/MlX3RH

![CPURayTrace_36](Images/CPURayTrace_36.jpg)

https://www.shadertoy.com/view/tl23Rm

![CPURayTrace_37](Images/CPURayTrace_37.jpg)

-----------------

ctrl+c+v被磨平了! 打开Dota2,奖励自己一把炸弹人,开心下! 我不想回老家相亲呀,心好累!