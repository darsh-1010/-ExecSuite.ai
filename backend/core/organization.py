"""
Organization class that orchestrates the team of agents based on the selected department
to execute collaborative or sequential campaigns.
"""

import logging
from typing import Dict, Optional

from core.agent import Agent, get_persona_config
from core.llm_wrapper import LLMWrapper
from core.memory import SharedMemory

logger = logging.getLogger(__name__)

# Pre-configured business departments and their campaign templates
DEPARTMENTS = {
    "c_suite": {
        "name": "C-Suite Leadership Suite",
        "agents": ["CEO", "CFO", "CMO", "Developer"],
        "sequence": ["CEO", "CFO", "CMO", "Developer", "CFO", "CMO", "Developer", "CEO"],
        "phases": [
            {
                "role": "CEO",
                "phase_name": "Planning & Scope Definition",
                "instructions": (
                    "Create a high-level roadmap and feature list for the task. "
                    "Write it to 'plan.md' in the workspace."
                )
            },
            {
                "role": "CFO",
                "phase_name": "Financial Modeling & Monetization",
                "instructions": (
                    "Review the roadmap in 'plan.md' and construct a budget analysis and pricing strategy. "
                    "Write it to 'budget_analysis.md' in the workspace."
                )
            },
            {
                "role": "CMO",
                "phase_name": "Branding & Marketing Strategy",
                "instructions": (
                    "Review 'plan.md' and write product marketing copy, slogans, and acquisition plan. "
                    "Write it to 'marketing_strategy.md' in the workspace."
                )
            },
            {
                "role": "Developer",
                "phase_name": "Technical Implementation",
                "instructions": (
                    "Review the specs, budget limits, and marketing copy. "
                    "Write the source code files (e.g. index.html, style.css, app.js, or backend scripts) "
                    "into the workspace. Ensure all files are production-ready."
                )
            },
            {
                "role": "CEO",
                "phase_name": "Executive Review & Summary",
                "instructions": (
                    "Review all generated documents and code files in the workspace. "
                    "Compile a final project summary report and write it to 'summary.md' in the workspace."
                )
            }
        ]
    },
    "marketing_campaign": {
        "name": "Marketing Campaign Suite",
        "agents": ["Product_Marketer", "Copywriter", "Social_Media_Manager", "SEO_Strategist"],
        "sequence": [
            "Product_Marketer",
            "Copywriter",
            "Social_Media_Manager",
            "SEO_Strategist",
            "Copywriter",
            "Product_Marketer"
        ],
        "phases": [
            {
                "role": "Product_Marketer",
                "phase_name": "Campaign Strategy & Brief",
                "instructions": (
                    "Define campaign objectives, target audience demographics, channels, and core messages. "
                    "Write details to 'campaign_brief.md' in the workspace."
                )
            },
            {
                "role": "Copywriter",
                "phase_name": "Marketing Copywriting",
                "instructions": (
                    "Write ad copy, email newsletter templates, and landing page "
                    "headlines based on 'campaign_brief.md'. "
                    "Save to 'ad_copy.md' in the workspace."
                )
            },
            {
                "role": "Social_Media_Manager",
                "phase_name": "Content Post Calendar",
                "instructions": (
                    "Design a 14-day social media post schedule (LinkedIn, X, "
                    "Instagram) based on the content in 'ad_copy.md'. "
                    "Save to 'social_schedule.md' in the workspace."
                )
            },
            {
                "role": "SEO_Strategist",
                "phase_name": "SEO Keyword Optimization",
                "instructions": (
                    "Review and optimize the calendar and copy for organic search keywords, metadata recommendations, "
                    "and link building options. Save to 'seo_brief.md' in the workspace."
                )
            },
            {
                "role": "Product_Marketer",
                "phase_name": "Campaign Launch Plan",
                "instructions": (
                    "Compile a marketing execution summary and KPIs report "
                    "in 'marketing_plan.md' linking the draft files."
                )
            }
        ]
    },
    "sales_campaign": {
        "name": "Sales Outreach Suite",
        "agents": ["Sales_Director", "Lead_Researcher", "Outreach_Specialist", "Customer_Advocate"],
        "sequence": [
            "Sales_Director",
            "Lead_Researcher",
            "Outreach_Specialist",
            "Customer_Advocate",
            "Outreach_Specialist",
            "Sales_Director"
        ],
        "phases": [
            {
                "role": "Sales_Director",
                "phase_name": "Sales Strategy & Target Definition",
                "instructions": (
                    "Define sales targets, value propositions, pricing tiers, and objection handling guidelines. "
                    "Save to 'sales_strategy.md' in the workspace."
                )
            },
            {
                "role": "Lead_Researcher",
                "phase_name": "Target Account Profiling",
                "instructions": (
                    "Define the Ideal Customer Profile (ICP), search criteria, "
                    "list typical target companies and contacts. "
                    "Save to 'target_prospects.md' in the workspace."
                )
            },
            {
                "role": "Outreach_Specialist",
                "phase_name": "Outbound Email Sequencing",
                "instructions": (
                    "Develop cold outbound email sequences (3 steps: introduction, "
                    "value add, follow up) tailored to 'target_prospects.md'. "
                    "Save to 'outbound_sequences.md' in the workspace."
                )
            },
            {
                "role": "Customer_Advocate",
                "phase_name": "Buyer Friction Review",
                "instructions": (
                    "Review outreach emails from the buyer perspective, listing "
                    "prospective objections and writing replies. "
                    "Save to 'objection_guide.md' in the workspace."
                )
            },
            {
                "role": "Sales_Director",
                "phase_name": "Outreach Playbook Release",
                "instructions": (
                    "Review and sign off outbound strategy, compiling a master "
                    "sales execution runbook in 'sales_runbook.md'."
                )
            }
        ]
    },
    "tech_development": {
        "name": "Tech Development Suite",
        "agents": ["Product_Manager", "Software_Architect", "Developer", "QA_Engineer"],
        "sequence": [
            "Product_Manager",
            "Software_Architect",
            "Developer",
            "QA_Engineer",
            "Developer",
            "Product_Manager"
        ],
        "phases": [
            {
                "role": "Product_Manager",
                "phase_name": "Product Requirements (PRD)",
                "instructions": (
                    "Write a product requirements document detailing user stories, features, and success metrics. "
                    "Save to 'requirements.md' in the workspace."
                )
            },
            {
                "role": "Software_Architect",
                "phase_name": "System Component Design",
                "instructions": (
                    "Design database schemas, component structures, API specs, and technical stack selection. "
                    "Save to 'system_architecture.md' in the workspace."
                )
            },
            {
                "role": "Developer",
                "phase_name": "Software Implementation",
                "instructions": (
                    "Write clean, fully functional code (HTML, CSS, JS, or "
                    "python) in the workspace based on the system design specs. "
                    "Save files inside the workspace."
                )
            },
            {
                "role": "QA_Engineer",
                "phase_name": "Quality Assurance & Test Plan",
                "instructions": (
                    "Review the code implementation, outline test plans, edge cases, and verification checklists. "
                    "Save to 'test_plan.md' in the workspace."
                )
            },
            {
                "role": "Product_Manager",
                "phase_name": "Release Summary",
                "instructions": (
                    "Review files and compile user release notes, installation setup guidelines, and launch summary "
                    "in 'release_notes.md' in the workspace."
                )
            }
        ]
    }
}


class Organization:
    """
    Orchestrator that sets up agents and executes workflows dynamically based on department configurations.
    """

    def __init__(
        self,
        memory: SharedMemory,
        llm_provider: Optional[str] = None,
        active_model: Optional[str] = None,
        department: str = "c_suite"
    ) -> None:
        """
        Initialize the Organization.

        Args:
            memory: SharedMemory instance.
            llm_provider: Optional provider override name.
            active_model: Optional model override name.
            department: The selected active department.
        """
        self.memory = memory
        self.llm_provider = llm_provider
        self.active_model = active_model
        self.department = department

        # Configure LLM
        self.llm = LLMWrapper(provider=llm_provider, model=active_model)

        # Initialize default agents
        self.agents: Dict[str, Agent] = {}
        self.setup_default_agents(department=department)

        # Running state
        self.is_running = False

    def setup_default_agents(self, department: str = "c_suite") -> None:
        """
        Initialize the agents for the selected department.

        Args:
            department: Key of the department in DEPARTMENTS config.
        """
        self.department = department
        self.agents.clear()

        dep_config = DEPARTMENTS.get(department, DEPARTMENTS["c_suite"])
        for role in dep_config["agents"]:
            persona = get_persona_config(role)
            self.agents[role] = Agent(
                persona["name"],
                persona["role"],
                persona["system_prompt"],
                llm=self.llm,
                memory=self.memory
            )

    def update_agent_persona(self, role: str, name: str, system_prompt: str) -> None:
        """
        Dynamically update an agent's persona.

        Args:
            role: The agent's role identifier.
            name: New name for the agent.
            system_prompt: New prompt defining behavior guidelines.
        """
        if role in self.agents:
            self.agents[role].name = name
            self.agents[role].system_prompt = system_prompt
            logger.info(f"[PERSONA_UPDATED] Role: {role} | Name: {name}")

    def _build_history_string(self) -> str:
        """
        Format the short-term conversation logs for LLM context.

        Returns:
            Pre-formatted string of conversation history.
        """
        history = []
        for msg in self.memory.get_messages():
            history.append(f"{msg['sender']} ({msg['role']}): {msg['content']}")
        return "\n\n".join(history)

    def run_task(self, task_description: str, workflow_type: str = "collaborative") -> None:
        """
        Execute a task using the specified workflow.

        Args:
            task_description: Core goal to achieve.
            workflow_type: Collaborative or sequential workflow mode.
        """
        if self.is_running:
            raise RuntimeError("An organization task is already running.")

        self.is_running = True
        self.memory.clear()

        self.memory.log_event("task_start", f"Starting task: {task_description}", {"workflow": workflow_type})

        try:
            if workflow_type == "sequential":
                self._run_sequential_workflow(task_description)
            else:
                self._run_collaborative_workflow(task_description)

            self.memory.log_event("task_end", "Task completed successfully!")
        except Exception as ex:
            logger.error(f"[WORKFLOW_ERROR] Error: {ex}", exc_info=True)
            self.memory.log_event("task_error", f"Task failed with error: {ex}")
            raise ex
        finally:
            self.is_running = False

    def _run_collaborative_workflow(self, task_description: str) -> None:
        """
        Round-table discussion style workflow.
        Agents take turns sharing ideas, refining them, and writing files.

        Args:
            task_description: The description of the task to run.
        """
        dep_config = DEPARTMENTS.get(self.department, DEPARTMENTS["c_suite"])
        turn_sequence = dep_config["sequence"]

        for turn_idx, role in enumerate(turn_sequence):
            agent = self.agents.get(role)
            if not agent:
                continue

            self.memory.log_event(
                "agent_turn",
                f"Active Agent: {agent.name} ({agent.role})",
                {"role": role, "turn": turn_idx}
            )

            history_str = self._build_history_string()
            response = agent.think_and_speak(task_description, history_str)

            # Save response to memory (broadcasts to UI)
            self.memory.add_message(agent.name, agent.role, response)

    def _run_sequential_workflow(self, task_description: str) -> None:
        """
        Waterfall sequential pipeline workflow.
        Each agent completes a specific deliverable phase and writes files.

        Args:
            task_description: The description of the task to run.
        """
        dep_config = DEPARTMENTS.get(self.department, DEPARTMENTS["c_suite"])
        phases = dep_config["phases"]

        for phase_idx, phase in enumerate(phases):
            role = phase["role"]
            agent = self.agents.get(role)
            if not agent:
                continue

            self.memory.log_event(
                "phase_start",
                f"Phase {phase_idx+1}: {phase['phase_name']} - Active Agent: {agent.name} ({agent.role})",
                {"role": role, "phase": phase["phase_name"]}
            )

            # Build custom instruction for sequential phase
            phase_prompt = f"\nCurrent Phase: {phase['phase_name']}\nYour Phase Instructions: {phase['instructions']}\n"

            history_str = self._build_history_string()
            combined_task = f"{task_description}\n\n{phase_prompt}"

            response = agent.think_and_speak(combined_task, history_str)
            self.memory.add_message(agent.name, agent.role, response)
