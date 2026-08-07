from django.core.management.base import BaseCommand

from ki_radar.core.llm_policy import get_accelerator_llm_policy


class Command(BaseCommand):
    help = "Zeigt die effektiv geladenen Accelerator-LLM-Limits ohne Secrets."

    def handle(self, *args, **options):
        policy = get_accelerator_llm_policy()
        self.stdout.write(f"timeout_seconds={policy.timeout_seconds}")
        self.stdout.write(f"max_input_chars={policy.max_input_chars}")
        self.stdout.write(f"shared_max_output_tokens={policy.max_output_tokens}")
        self.stdout.write(
            f"solution_generation_max_output_tokens={policy.solution_generation_max_output_tokens}"
        )
        self.stdout.write(
            "solution_generation_max_calls_per_context="
            f"{policy.solution_generation_max_calls_per_context}"
        )
        self.stdout.write(f"max_calls_per_user_day={policy.max_calls_per_user_day}")
        self.stdout.write(f"max_calls_global_day={policy.max_calls_global_day}")
