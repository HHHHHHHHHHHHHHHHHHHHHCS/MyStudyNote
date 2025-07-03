import time
from winotify import Notification

from jenkins import Jenkins

username = None
api_token = None
job_name = None

if __name__ == "__main__":
	last_result_build_number = None
	jen = Jenkins(url=None, username=username, password=api_token)

	while True:
		# 获取最后一次构建号
		last_build_number = jen.get_job_info(job_name)['lastBuild']['number']

		if last_result_build_number == last_build_number:
			time.sleep(5)
			continue

		# 获取该构建信息
		build_info = jen.get_build_info(job_name, last_build_number)

		result = build_info['result']

		if not result:
			time.sleep(5)
		else:
			last_result_build_number = last_build_number

			params = build_info['actions'][0]['parameters']

			platformtarget = "未知平台"

			for p in params:
				if p["name"] == "platformtarget":
					platformtarget = p["value"]
					break

			if result == "FAILURE":
				tips = " 打包失败!"
			elif result == "SUCCESS":
				tips = "打包成功!"
			else:
				tips = "打包未知!"

			toast = Notification(
				app_id="Jenkins",
				title= f"{platformtarget} {tips}",
				msg=tips)
				

			toast.set_audio(sound=None, loop=False)
			toast.show()