import os
import tarfile
import time
import requests
import google.auth
from google.auth.transport.requests import AuthorizedSession
from google.cloud import storage

PROJECT_ID = "coolops-bf6a0"
KEY_FILE = "coolops-bf6a0-firebase-adminsdk-fbsvc-4c24ea50a0.json"
BUCKET_NAME = "coolops-bf6a0_cloudbuild"
REGION = "us-central1"
SERVICE_NAME = "cool-ops-app"
IMAGE_NAME = f"gcr.io/{PROJECT_ID}/{SERVICE_NAME}"

def make_archive():
    print("1. Proje dosyaları arşivleniyor...")
    archive_path = "source.tar.gz"
    
    # Exclude files
    excludes = [
        "venv", "node_modules", ".git", ".github", ".idea", ".vscode",
        KEY_FILE, "source.tar.gz", "db.sqlite3", "deploy_runner.py",
        "staticfiles", "media"
    ]
    
    def filter_func(tarinfo):
        for ex in excludes:
            if tarinfo.name == ex or tarinfo.name.startswith(ex + "/"):
                return None
        return tarinfo

    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(".", filter=filter_func)
    print(f"   Arşiv hazırlandı: {archive_path}")
    return archive_path

def upload_to_gcs(archive_path):
    print(f"2. Arşiv GCS bucket'ına yükleniyor ({BUCKET_NAME})...")
    storage_client = storage.Client.from_service_account_json(KEY_FILE)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob("source.tar.gz")
    blob.upload_from_filename(archive_path)
    print("   Arşiv başarıyla yüklendi.")

def get_auth_session():
    credentials, project = google.auth.load_credentials_from_file(
        KEY_FILE,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    session = AuthorizedSession(credentials)
    return session

def run_cloud_build(session):
    print("3. Cloud Build üzerinde Docker imajı inşa ediliyor...")
    url = f"https://cloudbuild.googleapis.com/v1/projects/{PROJECT_ID}/locations/global/builds"
    
    payload = {
        "source": {
            "storageSource": {
                "bucket": BUCKET_NAME,
                "object": "source.tar.gz"
            }
        },
        "steps": [
            {
                "name": "gcr.io/cloud-builders/docker",
                "args": [
                    "build",
                    "-t",
                    IMAGE_NAME,
                    "."
                ]
            },
            {
                "name": "gcr.io/cloud-builders/docker",
                "args": [
                    "push",
                    IMAGE_NAME
                ]
            }
        ],
        "images": [
            IMAGE_NAME
        ]
    }
    
    res = session.post(url, json=payload)
    if res.status_code != 200:
        raise Exception(f"Cloud Build başlatılamadı: {res.text}")
    
    build_data = res.json()
    build_id = build_data["metadata"]["build"]["id"]
    print(f"   Build başlatıldı. ID: {build_id}")
    
    # Poll build status
    status_url = f"https://cloudbuild.googleapis.com/v1/projects/{PROJECT_ID}/locations/global/builds/{build_id}"
    while True:
        poll_res = session.get(status_url)
        if poll_res.status_code != 200:
            print("   Build durumu sorgulanamadı, tekrar deneniyor...")
            time.sleep(10)
            continue
        
        data = poll_res.json()
        status = data.get("status")
        print(f"   Mevcut durum: {status}")
        
        if status in ["SUCCESS"]:
            print("   Docker imajı başarıyla oluşturuldu ve yüklendi.")
            break
        elif status in ["FAILURE", "INTERNAL_ERROR", "CANCELLED", "TIMEOUT"]:
            raise Exception(f"Build başarısız oldu. Durum: {status}")
        
        time.sleep(15)

def deploy_to_cloud_run(session):
    print(f"4. Cloud Run servisi dağıtılıyor ({SERVICE_NAME})...")
    
    service_url = f"https://{REGION}-run.googleapis.com/apis/serving.knative.dev/v1/namespaces/{PROJECT_ID}/services/{SERVICE_NAME}"
    
    # Check if service exists
    res = session.get(service_url)
    exists = res.status_code == 200
    
    service_spec = {
        "apiVersion": "serving.knative.dev/v1",
        "kind": "Service",
        "metadata": {
            "name": SERVICE_NAME,
            "namespace": PROJECT_ID,
            "labels": {
                "cloud.googleapis.com/location": REGION
            }
        },
        "spec": {
            "template": {
                "spec": {
                    "containers": [
                        {
                            "image": IMAGE_NAME,
                            "ports": [
                                {
                                    "containerPort": 80
                                }
                            ],
                            "env": [
                                {
                                    "name": "DJANGO_SETTINGS_MODULE",
                                    "value": "config.settings"
                                }
                            ]
                        }
                    ]
                }
            }
        }
    }
    
    if exists:
        print("   Mevcut servis güncelleniyor...")
        # Get metadata to preserve resourceVersion
        current_data = res.json()
        service_spec["metadata"]["resourceVersion"] = current_data["metadata"]["resourceVersion"]
        deploy_res = session.put(service_url, json=service_spec)
    else:
        print("   Yeni servis oluşturuluyor...")
        create_url = f"https://{REGION}-run.googleapis.com/apis/serving.knative.dev/v1/namespaces/{PROJECT_ID}/services"
        deploy_res = session.post(create_url, json=service_spec)
        
    if deploy_res.status_code not in [200, 201]:
        raise Exception(f"Cloud Run dağıtımı başarısız: {deploy_res.text}")
        
    print("   Cloud Run servisi başarıyla dağıtıldı.")
    
    # Make service public (allow unauthenticated)
    print("   Servis dış dünyaya erişime açılıyor (allow unauthenticated)...")
    iam_url = f"https://us-central1-run.googleapis.com/v1/projects/{PROJECT_ID}/locations/{REGION}/services/{SERVICE_NAME}:setIamPolicy"
    iam_payload = {
        "policy": {
            "bindings": [
                {
                    "role": "roles/run.invoker",
                    "members": [
                        "allUsers"
                    ]
                }
            ]
        }
    }
    iam_res = session.post(iam_url, json=iam_payload)
    if iam_res.status_code != 200:
        print(f"   UYARI: Servis dış dünyaya açılamadı: {iam_res.text}")
    else:
        print("   Servis dış dünyaya başarıyla açıldı.")

def main():
    start_time = time.time()
    archive_path = None
    try:
        archive_path = make_archive()
        upload_to_gcs(archive_path)
        
        session = get_auth_session()
        run_cloud_build(session)
        deploy_to_cloud_run(session)
        
        print("5. Firebase Hosting kuralları dağıtılıyor...")
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(KEY_FILE)
        # Run local firebase deploy using npx
        import subprocess
        # We need shell=True on Windows
        sub_res = subprocess.run("npx firebase deploy --only hosting", shell=True)
        if sub_res.returncode != 0:
            raise Exception("Firebase Hosting dağıtımı başarısız oldu.")
            
        print(f"\nTEBRİKLER! Dağıtım başarıyla tamamlandı. Toplam süre: {int(time.time() - start_time)} saniye.")
        print(f"Uygulamanız şu adreste aktif: https://{PROJECT_ID}.web.app")
        
    except Exception as e:
        print(f"\nHATA OLUŞTU: {e}")
    finally:
        if archive_path and os.path.exists(archive_path):
            os.remove(archive_path)

if __name__ == "__main__":
    main()
