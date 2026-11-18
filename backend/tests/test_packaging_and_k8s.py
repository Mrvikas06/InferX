"""Tests for Production Packaging, Docker, Docker Compose, and Kubernetes Manifests."""

from pathlib import Path
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_dockerfiles_structure():
    """Verify backend and frontend Dockerfiles have multi-stage builds and security best practices."""
    backend_df = REPO_ROOT / "backend" / "Dockerfile"
    frontend_df = REPO_ROOT / "frontend" / "Dockerfile"

    assert backend_df.exists(), "backend/Dockerfile must exist"
    assert frontend_df.exists(), "frontend/Dockerfile must exist"

    b_content = backend_df.read_text(encoding="utf-8")
    assert "AS builder" in b_content, "Backend Dockerfile should have builder stage"
    assert "AS runtime" in b_content, "Backend Dockerfile should have runtime stage"
    assert "USER inferx" in b_content, "Backend should run as non-root user"
    assert "HEALTHCHECK" in b_content, "Backend Dockerfile must define HEALTHCHECK"

    f_content = frontend_df.read_text(encoding="utf-8")
    assert "AS builder" in f_content, "Frontend Dockerfile should have builder stage"
    assert "AS runner" in f_content, "Frontend Dockerfile should have runner stage"
    assert "USER nextjs" in f_content, "Frontend should run as non-root nextjs user"
    assert "HEALTHCHECK" in f_content, "Frontend Dockerfile must define HEALTHCHECK"


def test_docker_compose_validity():
    """Verify docker-compose.yml and docker-compose.prod.yml have required services and volumes."""
    dev_compose = REPO_ROOT / "docker-compose.yml"
    prod_compose = REPO_ROOT / "docker-compose.prod.yml"

    assert dev_compose.exists()
    assert prod_compose.exists()

    dev_data = yaml.safe_load(dev_compose.read_text(encoding="utf-8"))
    prod_data = yaml.safe_load(prod_compose.read_text(encoding="utf-8"))

    for compose in (dev_data, prod_data):
        assert "services" in compose
        services = compose["services"]
        assert "postgres" in services
        assert "redis" in services
        assert "backend" in services
        assert "frontend" in services
        assert "volumes" in compose


def test_kubernetes_manifests():
    """Verify Kubernetes YAML syntax and presence of all essential workload definitions."""
    k8s_dir = REPO_ROOT / "deploy" / "k8s"
    assert k8s_dir.exists()

    expected_files = [
        "namespace.yaml",
        "configmap.yaml",
        "secrets.yaml",
        "postgres.yaml",
        "redis.yaml",
        "backend.yaml",
        "frontend.yaml",
        "ingress.yaml",
        "hpa.yaml",
        "kustomization.yaml",
    ]

    for fname in expected_files:
        path = k8s_dir / fname
        assert path.exists(), f"Missing K8s manifest: {fname}"
        # Validate that each file parses as valid YAML
        content = path.read_text(encoding="utf-8")
        docs = list(yaml.safe_load_all(content))
        assert len(docs) >= 1, f"Manifest {fname} has empty YAML"


def test_helm_chart_validity():
    """Verify Helm chart Chart.yaml, values.yaml, and templates."""
    helm_dir = REPO_ROOT / "deploy" / "helm" / "inferx"
    assert helm_dir.exists()

    chart_file = helm_dir / "Chart.yaml"
    values_file = helm_dir / "values.yaml"
    templates_dir = helm_dir / "templates"

    assert chart_file.exists()
    assert values_file.exists()
    assert templates_dir.exists()

    chart_data = yaml.safe_load(chart_file.read_text(encoding="utf-8"))
    assert chart_data["name"] == "inferx"
    assert "version" in chart_data

    values_data = yaml.safe_load(values_file.read_text(encoding="utf-8"))
    assert "backend" in values_data
    assert "frontend" in values_data
    assert "ingress" in values_data
    assert "postgresql" in values_data
    assert "redis" in values_data

    # Check key template files
    for tmpl in ["backend.yaml", "frontend.yaml", "ingress.yaml", "configmap.yaml", "secrets.yaml"]:
        assert (templates_dir / tmpl).exists()


def test_smoke_test_script_exists():
    """Verify smoke test script exists."""
    smoke_script = REPO_ROOT / "scripts" / "prod_smoke_test.py"
    assert smoke_script.exists()
    content = smoke_script.read_text(encoding="utf-8")
    assert "run_smoke_tests" in content
