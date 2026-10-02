Run Test Phenobase in detached mode
```bash
docker compose up -d
```

Status of Container
```bash
docker compose ps
```
Stop and delete container
```bash
docker compose down 
```
Delete persisten volume
```bash
docker volume rm docker_pgdata
```
Check Config
```bash
docker compose config
```

