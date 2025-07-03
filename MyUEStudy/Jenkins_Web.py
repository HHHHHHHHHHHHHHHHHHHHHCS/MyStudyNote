import requests
from requests.auth import HTTPBasicAuth

# Jenkins 信息
jenkins_url = None
jenkins_user = None
jenkins_token = None

headers = {
	"Content-Type": "application/x-www-form-urlencoded"
}

body_str_compile = None

body_str_pc = None

class JenkinsCls:
	COMPILE_P4 = 0
	COMPILE_GIT = 1
	BUILD_PC = 2
	BUILD_ANDROID = 3

	@staticmethod
	def exec_jenkins(arg_type):

		body_str = None
		if arg_type == JenkinsCls.COMPILE_P4:
			body_str = body_str_compile
		elif arg_type == JenkinsCls.BUILD_PC:
			body_str = body_str_pc

		if body_str is None:
			out_str = f"不支持的arg_type: {arg_type}"
			print(out_str)
			return False, out_str

		# 触发构建
		response = requests.post(
			jenkins_url,
			auth = HTTPBasicAuth(jenkins_user, jenkins_token),
			headers = headers,
			data = body_str
		)

		# 输出返回信息
		if 200 <= response.status_code < 300:
			print("Jenkins成功触发！")
			return True, "Jenkins触发成功"
		else:
			print(f"Jenkins触发失败: {response.status_code}, {response.text}")
			return False, "Jenkins触发失败"