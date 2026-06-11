from smbclient import register_session, listdir, open_file
from dotenv import load_dotenv
import os 

load_dotenv()


user = os.environ["NORMAL_USER"]
password = os.environ["NORMAL_USER_PW"]

unc_mirror = os.environ["UNC_MIRROR"]
unc_origin = os.environ["UNC_ORIGIN"]

host_mirror = os.environ["HOST_MIRROR"]
host_origin = os.environ["HOST_ORIGIN"]



print(f"User: {user}")
print(f"Password: {password}")
print(f"UNC Mirror: {unc_mirror}")
print(f"UNC Origin: {unc_origin}")


register_session(host_origin, username=user, password=password)
register_session

for f in listdir(unc_origin):
    print(f.filename if hasattr(f, 'filename') else f)


# register_session(
#     os.getenv("SMB_HOST_MIRROR"), 
#     username=os.getenv("SMB_USER"), 
#     password=os.getenv("SMB_PASS")
# )

# print(listdir(f"\\\\{os.getenv('SMB_HOST_MIRROR')}\\{os.getenv('SMB_SHARE')}\\{os.getenv('SMB_PATH')}"))