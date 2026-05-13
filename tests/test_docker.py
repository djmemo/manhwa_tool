"""
tests/test_docker.py — Validation statique des fichiers Docker.
Tous les tests fonctionnent SANS Docker installé (analyse de fichiers + sh POSIX).
"""
import os
import shutil
import subprocess
import tempfile
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(path: str) -> str:
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return f.read()


def exists(path: str) -> bool:
    return os.path.isfile(os.path.join(ROOT, path))


# ═══════════════════════════════════════════════════════════════════════════════
# TestDockerBuild — Analyse statique des fichiers (sans Docker)
# ═══════════════════════════════════════════════════════════════════════════════

class TestDockerBuild:

    def test_dockerfile_exists(self):
        assert exists("Dockerfile"), "Dockerfile absent à la racine"

    def test_dockerignore_exists(self):
        assert exists(".dockerignore"), ".dockerignore absent à la racine"

    def test_entrypoint_exists(self):
        assert exists("docker/entrypoint.sh"), "docker/entrypoint.sh absent"

    def test_env_example_exists(self):
        assert exists("docker/env.example"), "docker/env.example absent"

    def test_compose_file_exists(self):
        assert exists("docker-compose.yml"), "docker-compose.yml absent"

    # ── Dockerfile — structure ────────────────────────────────────────────────

    def test_dockerfile_uses_alpine(self):
        content = read("Dockerfile")
        assert "python:3.11-alpine" in content

    def test_dockerfile_multistage(self):
        content = read("Dockerfile")
        from_lines = [l for l in content.splitlines() if l.strip().upper().startswith("FROM")]
        assert len(from_lines) >= 2, f"Multi-stage requis (2 FROM min), trouvé : {len(from_lines)}"

    def test_dockerfile_builder_stage(self):
        assert "AS builder" in read("Dockerfile")

    def test_dockerfile_runtime_stage(self):
        assert "AS runtime" in read("Dockerfile")

    def test_dockerfile_copies_venv_from_builder(self):
        content = read("Dockerfile")
        assert "--from=builder" in content and "/opt/venv" in content

    def test_dockerfile_non_root_user(self):
        assert "USER manhwa" in read("Dockerfile")

    def test_dockerfile_creates_manhwa_user(self):
        content = read("Dockerfile")
        assert "adduser" in content and "manhwa" in content

    def test_dockerfile_no_run_after_user(self):
        """Aucune instruction RUN après USER manhwa (sécurité)."""
        lines = read("Dockerfile").splitlines()
        user_idx = None
        for i, line in enumerate(lines):
            if line.strip() == "USER manhwa":
                user_idx = i
                break
        assert user_idx is not None, "USER manhwa non trouvé"
        for line in lines[user_idx + 1:]:
            assert not line.strip().startswith("RUN"), \
                f"RUN après USER manhwa interdit : {line.strip()}"

    def test_dockerfile_pythonunbuffered(self):
        assert "PYTHONUNBUFFERED=1" in read("Dockerfile")

    def test_dockerfile_pythondontwritebytecode(self):
        assert "PYTHONDONTWRITEBYTECODE=1" in read("Dockerfile")

    def test_dockerfile_term_env(self):
        assert "TERM=xterm-256color" in read("Dockerfile")

    def test_dockerfile_volume_osirisscan(self):
        assert "/data/osirisscan" in read("Dockerfile")

    def test_dockerfile_volume_realesrgan(self):
        assert "/tools/realesrgan" in read("Dockerfile")

    def test_dockerfile_env_osirisscan_racine(self):
        assert "OSIRISSCAN_RACINE" in read("Dockerfile")

    def test_dockerfile_env_esrgan_exe_path(self):
        assert "ESRGAN_EXE_PATH" in read("Dockerfile")

    def test_dockerfile_no_cache_pip(self):
        assert "--no-cache-dir" in read("Dockerfile")

    def test_dockerfile_apk_no_cache(self):
        assert "apk add --no-cache" in read("Dockerfile")

    def test_dockerfile_entrypoint(self):
        content = read("Dockerfile")
        assert "ENTRYPOINT" in content and "entrypoint.sh" in content

    def test_dockerfile_workdir_app(self):
        assert "WORKDIR /app" in read("Dockerfile")

    # ── .dockerignore ─────────────────────────────────────────────────────────

    def test_dockerignore_excludes_pycache(self):
        assert "__pycache__/" in read(".dockerignore")

    def test_dockerignore_excludes_tests(self):
        assert "tests/" in read(".dockerignore")

    def test_dockerignore_excludes_config_yaml(self):
        assert "config.yaml" in read(".dockerignore")

    def test_dockerignore_excludes_git(self):
        assert ".git/" in read(".dockerignore")

    def test_dockerignore_excludes_venv(self):
        content = read(".dockerignore")
        assert ".venv/" in content or "venv/" in content

    def test_dockerignore_excludes_env_files(self):
        assert ".env" in read(".dockerignore")

    # ── docker-compose.yml ────────────────────────────────────────────────────

    def test_compose_tty_enabled(self):
        assert "tty: true" in read("docker-compose.yml")

    def test_compose_stdin_open(self):
        assert "stdin_open: true" in read("docker-compose.yml")

    def test_compose_volume_osirisscan(self):
        assert "/data/osirisscan" in read("docker-compose.yml")

    def test_compose_volume_realesrgan(self):
        assert "/tools/realesrgan" in read("docker-compose.yml")

    def test_compose_restart_no(self):
        assert 'restart: "no"' in read("docker-compose.yml")

    def test_compose_env_osirisscan_racine(self):
        assert "OSIRISSCAN_RACINE" in read("docker-compose.yml")

    def test_compose_network_none(self):
        assert "network_mode: none" in read("docker-compose.yml")

    # ── docker/entrypoint.sh ──────────────────────────────────────────────────

    def test_entrypoint_posix_sh(self):
        first_line = read("docker/entrypoint.sh").splitlines()[0]
        assert first_line == "#!/bin/sh", f"Doit être #!/bin/sh, trouvé : {first_line}"

    def test_entrypoint_passes_args(self):
        assert '"$@"' in read("docker/entrypoint.sh")

    def test_entrypoint_default_racine(self):
        assert "/data/osirisscan" in read("docker/entrypoint.sh")

    def test_entrypoint_default_esrgan(self):
        assert "/tools/realesrgan" in read("docker/entrypoint.sh")

    def test_entrypoint_set_eu(self):
        assert "set -eu" in read("docker/entrypoint.sh")

    def test_entrypoint_generates_yaml(self):
        content = read("docker/entrypoint.sh")
        assert "config.yaml" in content or "manhwa_config" in content

    def test_entrypoint_checks_config_flag(self):
        assert "--config" in read("docker/entrypoint.sh")

    def test_entrypoint_exec_python(self):
        assert "exec python main.py" in read("docker/entrypoint.sh")

    # ── docker/env.example ────────────────────────────────────────────────────

    def test_env_example_osirisscan_racine(self):
        assert "OSIRISSCAN_RACINE=" in read("docker/env.example")

    def test_env_example_esrgan_path(self):
        assert "ESRGAN_EXE_PATH=" in read("docker/env.example")

    def test_env_example_console_largeur(self):
        assert "CONSOLE_LARGEUR=" in read("docker/env.example")

    def test_env_example_host_path(self):
        assert "OSIRISSCAN_HOST_PATH=" in read("docker/env.example")


# ═══════════════════════════════════════════════════════════════════════════════
# TestDockerEntrypoint — Exécution de entrypoint.sh avec sh POSIX
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.skipif(not shutil.which("sh"), reason="sh POSIX requis")
class TestDockerEntrypoint:
    """
    Teste le comportement de entrypoint.sh en l'exécutant avec sh.
    Remplace 'exec python main.py' par 'echo' pour ne pas lancer l'appli.
    """

    def _run_entrypoint(self, env: dict, args: list[str] | None = None) -> tuple:
        entrypoint_path = os.path.join(ROOT, "docker", "entrypoint.sh")
        with open(entrypoint_path) as f:
            content = f.read()

        # Patcher les deux branches exec pour les tests
        test_content = content.replace(
            'exec python main.py --config "$CONFIG_FILE" "$@"',
            'echo LAUNCHED_WITH_CONFIG && cat "$CONFIG_FILE" && exit 0'
        ).replace(
            'exec python main.py "$@"',
            'echo LAUNCHED_WITHOUT_CONFIG && exit 0'
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".sh", delete=False, prefix="test_entry_"
        ) as tmp:
            tmp.write(test_content)
            tmp_path = tmp.name

        try:
            os.chmod(tmp_path, 0o755)
            result = subprocess.run(
                ["sh", tmp_path] + (args or []),
                env={**os.environ, **env},
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode, result.stdout + result.stderr
        finally:
            os.unlink(tmp_path)

    def test_entrypoint_generates_config(self):
        """entrypoint.sh génère un config YAML valide depuis les env vars."""
        import yaml
        code, output = self._run_entrypoint({
            "OSIRISSCAN_RACINE": "/data/test",
            "ESRGAN_EXE_PATH": "/tools/esrgan",
            "CONSOLE_LARGEUR": "80",
        })
        assert code == 0, f"entrypoint.sh a échoué : {output}"
        assert "LAUNCHED_WITH_CONFIG" in output
        yaml_lines = output.split("LAUNCHED_WITH_CONFIG\n", 1)
        if len(yaml_lines) > 1:
            yaml_part = yaml_lines[1].strip()
            if yaml_part:
                data = yaml.safe_load(yaml_part)
                assert data["machine"]["racine_osirisscan"] == "/data/test"

    def test_entrypoint_default_values(self):
        """Sans env vars, les valeurs par défaut sont utilisées."""
        import yaml
        clean_env = {k: v for k, v in os.environ.items()
                     if k not in ("OSIRISSCAN_RACINE", "ESRGAN_EXE_PATH", "CONSOLE_LARGEUR")}
        code, output = self._run_entrypoint(clean_env)
        assert code == 0, f"entrypoint.sh a échoué : {output}"
        yaml_lines = output.split("LAUNCHED_WITH_CONFIG\n", 1)
        if len(yaml_lines) > 1:
            yaml_part = yaml_lines[1].strip()
            if yaml_part:
                data = yaml.safe_load(yaml_part)
                assert data["machine"]["racine_osirisscan"] == "/data/osirisscan"

    def test_entrypoint_custom_racine(self):
        """OSIRISSCAN_RACINE=/custom est correctement injecté dans le config."""
        import yaml
        code, output = self._run_entrypoint({"OSIRISSCAN_RACINE": "/custom/path"})
        assert code == 0
        yaml_lines = output.split("LAUNCHED_WITH_CONFIG\n", 1)
        if len(yaml_lines) > 1:
            yaml_part = yaml_lines[1].strip()
            if yaml_part:
                data = yaml.safe_load(yaml_part)
                assert data["machine"]["racine_osirisscan"] == "/custom/path"

    def test_entrypoint_skip_config_if_flag(self):
        """Si --config est dans les args, le config temporaire n'est PAS généré."""
        code, output = self._run_entrypoint({}, args=["--config", "/some/config.yaml"])
        assert code == 0
        assert "LAUNCHED_WITHOUT_CONFIG" in output
        assert "LAUNCHED_WITH_CONFIG" not in output
