"""
tests/test_agents.py
---------------------
Test suite for BaseAgent, AgentRegistry, and all 3 specialist agents.

Run with:
    python tests/test_agents.py
    # -- or --
    python -m pytest tests/test_agents.py -v
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent      import BaseAgent
from agents.search_agent    import SearchAgent
from agents.analysis_agent  import AnalysisAgent
from agents.writing_agent   import WritingAgent
from core.agent_registry    import AgentRegistry

# ---------------------------------------------
#  Test harness
# ---------------------------------------------

PASS = " [OK] "
FAIL = " [FAIL] "
_results: list[tuple[str, bool]] = []

TEST_QUERY = "electric vehicles in India"


def test(label: str, condition: bool) -> None:
    status = PASS if condition else FAIL
    print(f"  {status}  {label}")
    _results.append((label, condition))


def section(title: str) -> None:
    print(f"\n{'-' * 60}")
    print(f"  {title}")
    print(f"{'-' * 60}")


# ---------------------------------------------
#  Dummy agent for BaseAgent tests
# ---------------------------------------------

class EchoAgent(BaseAgent):
    def execute(self, task: str) -> str:
        return f"[ECHO] {task}"


# ---------------------------------------------
#  BaseAgent suite  (identical to previous)
# ---------------------------------------------

def test_base_agent_creation() -> None:
    section("1 ? BaseAgent -- construction & defaults")
    agent = EchoAgent("EchoAgent", "Echoes tasks.", "testing", 0.5)
    test("name is set",                    agent.name == "EchoAgent")
    test("description is set",             agent.description == "Echoes tasks.")
    test("speciality is set",              agent.speciality == "testing")
    test("rate_per_task is set",           agent.rate_per_task == 0.5)
    test("wallet_address defaults ''",     agent.wallet_address == "")
    test("tasks_completed defaults 0",     agent.tasks_completed == 0)
    test("successful_tasks defaults 0",    agent.successful_tasks == 0)
    test("total_earned defaults 0.0",      agent.total_earned == 0.0)
    test("rating defaults 5.0",            agent.rating == 5.0)


def test_execute_abstract() -> None:
    section("2 ? BaseAgent -- execute() abstraction")
    agent  = EchoAgent("E2", "Echo", "testing", 0.5)
    result = agent.execute("hello")
    test("execute() returns string",       isinstance(result, str))
    test("execute() correct content",      result == "[ECHO] hello")
    try:
        class Broken(BaseAgent): pass
        Broken("X", "Y", "Z", 1.0)
        test("ABC blocks missing execute()", False)
    except TypeError:
        test("ABC blocks missing execute()", True)


def test_update_stats() -> None:
    section("3 ? BaseAgent -- update_stats() & rating")
    a = EchoAgent("S", "S", "testing", 1.0)
    a.update_stats(True,  1.0)
    test("tasks_completed -> 1",            a.tasks_completed == 1)
    test("rating stays 5.0 (1/1)",         a.rating == 5.0)
    a.update_stats(False, 0.0)
    test("tasks_completed -> 2",            a.tasks_completed == 2)
    test("rating drops to 2.5 (1/2)",      a.rating == 2.5)
    a.update_stats(True,  1.5)
    test("total_earned = 2.5",             round(a.total_earned, 4) == 2.5)
    test("rating ? 3.33 (2/3)",            a.rating == round((2/3)*5, 2))


def test_get_stats_shape() -> None:
    section("4 ? BaseAgent -- get_stats() schema")
    a = EchoAgent("G", "G", "testing", 2.0)
    a.update_stats(True, 2.0)
    s = a.get_stats()
    for key in ["name", "rating", "tasks_completed", "success_rate", "total_earned", "status"]:
        test(f"stats has '{key}'",         key in s)
    test("success_rate = 100.0",           s["success_rate"] == 100.0)
    test("status = 'available'",           s["status"] == "available")
    print(f"\n  get_stats() -> {s}")


def test_get_card_data() -> None:
    section("5 ? BaseAgent -- get_card_data() schema")
    a = EchoAgent("C", "Card agent", "testing", 3.0)
    c = a.get_card_data()
    for key in ["name", "description", "speciality", "rate_per_task",
                "rating", "tasks_completed", "success_rate", "status"]:
        test(f"card has '{key}'",          key in c)
    test("status always 'available'",      c["status"] == "available")


def test_agent_registry() -> None:
    section("6 ? AgentRegistry -- register, lookup, filter")
    reg = AgentRegistry()
    a1  = EchoAgent("Alpha", "A1", "search",  1.0)
    a2  = EchoAgent("Beta",  "A2", "writing", 2.0)
    a3  = EchoAgent("Gamma", "A3", "search",  1.5)
    reg.register_agent(a1)
    reg.register_agent(a2)
    reg.register_agent(a3)
    test("len(reg) == 3",                  len(reg) == 3)
    test("'Alpha' in reg",                 "Alpha" in reg)
    test("get_agent('Beta').name",         reg.get_agent("Beta").name == "Beta")
    try:
        reg.register_agent(EchoAgent("Alpha", "dup", "search", 1.0))
        test("duplicate raises ValueError", False)
    except ValueError:
        test("duplicate raises ValueError", True)
    try:
        reg.get_agent("NoSuch")
        test("missing raises KeyError",    False)
    except KeyError:
        test("missing raises KeyError",    True)
    test("filter by speciality == 2",      len(reg.get_agents_by_speciality("search")) == 2)


def test_marketplace_stats() -> None:
    section("7 ? AgentRegistry -- get_marketplace_stats()")
    reg = AgentRegistry()
    a1  = EchoAgent("W1", "w1", "analysis", 2.0)
    a2  = EchoAgent("W2", "w2", "writing",  3.0)
    a1.update_stats(True,  2.0)
    a1.update_stats(True,  2.0)
    a2.update_stats(False, 0.0)
    reg.register_agent(a1)
    reg.register_agent(a2)
    s = reg.get_marketplace_stats()
    test("total_agents == 2",             s["total_agents"] == 2)
    test("total_tasks_completed == 3",    s["total_tasks_completed"] == 3)
    test("total_usdc_paid_out == 4.0",    s["total_usdc_paid_out"] == 4.0)
    test("most_active_agent == 'W1'",     s["most_active_agent"] == "W1")
    print(f"\n  get_marketplace_stats() -> {s}")


# ---------------------------------------------
#  Specialist agent suites
# ---------------------------------------------

def test_search_agent() -> None:
    section("8 ? SearchAgent -- identity & execute()")

    agent = SearchAgent()

    # Identity checks
    test("name == 'Search Agent'",         agent.name == "Search Agent")
    test("speciality == 'Web Research'",   agent.speciality == "Web Research")
    test("rate_per_task == 0.1",           agent.rate_per_task == 0.10)
    test("is BaseAgent subclass",          isinstance(agent, BaseAgent))

    # Execute with mock (no real API key)
    print(f"\n  Calling execute('{TEST_QUERY}') ...")
    result = agent.execute(TEST_QUERY)
    print(f"  Raw output type: {type(result).__name__}")

    test("execute() returns dict",                isinstance(result, dict))
    test("result has 'results' key",              "results" in result)
    test("result has 'total_results' key",        "total_results" in result)
    test("result has 'query' key",                "query" in result)
    test("query echoed correctly",                result.get("query") == TEST_QUERY)
    test("'results' is a list",                   isinstance(result.get("results"), list))
    test("results list is non-empty",             len(result.get("results", [])) > 0)

    first = result["results"][0] if result["results"] else {}
    test("first result has 'title'",              "title" in first)
    test("first result has 'url'",                "url" in first)
    test("first result has 'summary'",            "summary" in first)
    test("first result has 'relevance'",          "relevance" in first)
    test("relevance is float 0.0?1.0",            0.0 <= first.get("relevance", -1) <= 1.0)
    test("total_results matches list length",     result["total_results"] == len(result["results"]))

    print(f"\n  SearchAgent result preview:")
    for r in result["results"][:2]:
        print(f"    ? [{r['relevance']}] {r['title']}")
        print(f"      {r['url']}")


def test_analysis_agent() -> None:
    section("9 ? AnalysisAgent -- identity & execute()")

    agent = AnalysisAgent()

    # Identity checks
    test("name == 'Analysis Agent'",       agent.name == "Analysis Agent")
    test("speciality == 'Data Analysis'",  agent.speciality == "Data Analysis")
    test("rate_per_task == 0.1",           agent.rate_per_task == 0.10)
    test("is BaseAgent subclass",          isinstance(agent, BaseAgent))

    # Build a realistic task string from mock search results
    task_input = (
        "Search results for 'electric vehicles in India':\n"
        "1. India EV market grew 49% to 1.67M units in FY2024. "
        "Two-wheelers lead with 59% share. Tata Motors dominates passenger EVs.\n"
        "2. FAME-II disbursed ?10,000 crore. Battery costs on track for $100/kWh by 2026.\n"
        "3. Charging infrastructure growing at 80% CAGR. Tier-2 cities emerging as growth frontier."
    )

    print(f"\n  Calling execute() with research content ...")
    result = agent.execute(task_input)
    print(f"  Raw output type: {type(result).__name__}")

    test("execute() returns dict",                    isinstance(result, dict))
    test("result has 'key_findings'",                 "key_findings" in result)
    test("result has 'trends'",                       "trends" in result)
    test("result has 'important_numbers'",            "important_numbers" in result)
    test("result has 'summary'",                      "summary" in result)
    test("'key_findings' is a non-empty list",        isinstance(result.get("key_findings"), list)
                                                      and len(result["key_findings"]) > 0)
    test("'trends' is a non-empty list",              isinstance(result.get("trends"), list)
                                                      and len(result["trends"]) > 0)
    test("'important_numbers' is a list",             isinstance(result.get("important_numbers"), list))
    test("'summary' is a non-empty string",           isinstance(result.get("summary"), str)
                                                      and len(result["summary"]) > 10)

    print(f"\n  AnalysisAgent result preview:")
    print(f"    key_findings[0]: {result['key_findings'][0][:80]}...")
    print(f"    trends[0]:       {result['trends'][0][:80]}...")
    print(f"    summary:         {result['summary'][:120]}...")


def test_writing_agent() -> None:
    section("10 ? WritingAgent -- identity & execute()")

    agent = WritingAgent()

    # Identity checks
    test("name == 'Writing Agent'",         agent.name == "Writing Agent")
    test("speciality == 'Report Writing'",  agent.speciality == "Report Writing")
    test("rate_per_task == 0.1",            agent.rate_per_task == 0.10)
    test("is BaseAgent subclass",           isinstance(agent, BaseAgent))

    # Build a realistic task string (mock analysis output)
    mock_analysis = {
        "key_findings": [
            "India EV market grew 49% to 1.67M units in FY2024.",
            "Tata Motors holds 70%+ passenger EV market share.",
            "FAME-II disbursed ?10,000 crore in subsidies.",
        ],
        "trends": [
            "Charging infrastructure growing at 80% CAGR.",
            "Battery costs projected to reach $100/kWh by 2026.",
            "Tier-2 cities emerging as next growth frontier.",
        ],
        "important_numbers": [
            "1.67 million EV units sold FY2024",
            "49% YoY growth",
            "?10,000 crore FAME-II disbursement",
        ],
        "summary": (
            "India's EV market is booming, driven by policy support and falling battery costs. "
            "Tata Motors leads as charging infrastructure expands rapidly."
        ),
    }
    task_input = json.dumps(mock_analysis, indent=2)

    print(f"\n  Calling execute() with analysis data ...")
    result = agent.execute(task_input)
    print(f"  Raw output type: {type(result).__name__}, length: {len(result)} chars")

    test("execute() returns str",                     isinstance(result, str))
    test("report is non-empty",                       len(result) > 100)

    # Check all 5 required sections exist
    required_sections = [
        "Executive Summary",
        "Key Findings",
        "Market Data",
        "Trends",
        "Conclusion",
    ]
    for section_name in required_sections:
        test(f"report has '## {section_name}' section",   section_name in result)

    print(f"\n  WritingAgent report preview (first 400 chars):")
    print("  " + result[:400].replace("\n", "\n  "))


def test_full_pipeline() -> None:
    section("11 ? Full Pipeline -- Search -> Analyse -> Write")

    print(f"\n  Running full pipeline for query: '{TEST_QUERY}'")

    # Step 1: Search
    search  = SearchAgent()
    s_out   = search.execute(TEST_QUERY)
    search.update_stats(success=True, amount_earned=2.0)

    # Step 2: Analyse
    analyse = AnalysisAgent()
    a_input = json.dumps(s_out, indent=2)
    a_out   = analyse.execute(a_input)
    analyse.update_stats(success=True, amount_earned=2.0)

    # Step 3: Write
    writer  = WritingAgent()
    w_input = json.dumps(a_out, indent=2)
    w_out   = writer.execute(w_input)
    writer.update_stats(success=True, amount_earned=2.0)

    test("Pipeline: search output is dict",     isinstance(s_out, dict))
    test("Pipeline: analysis output is dict",   isinstance(a_out, dict))
    test("Pipeline: report output is string",   isinstance(w_out, str))
    test("Pipeline: report length > 200 chars", len(w_out) > 200)

    # Check agent stats updated
    test("SearchAgent tasks_completed == 1",    search.tasks_completed == 1)
    test("AnalysisAgent tasks_completed == 1",  analyse.tasks_completed == 1)
    test("WritingAgent tasks_completed == 1",   writer.tasks_completed == 1)

    # Registry integration
    reg = AgentRegistry()
    reg.register_agent(search)
    reg.register_agent(analyse)
    reg.register_agent(writer)

    stats = reg.get_marketplace_stats()
    test("Marketplace total_agents == 3",       stats["total_agents"] == 3)
    test("Marketplace total_tasks == 3",        stats["total_tasks_completed"] == 3)
    test("Marketplace usdc_paid_out == 6.0",    stats["total_usdc_paid_out"] == 6.0)

    print(f"\n  Marketplace stats: {stats}")
    print(f"\n  Report snippet:\n")
    # Clean non-ASCII for Windows terminal safety
    safe_report = "".join([c if ord(c) < 128 else '?' for c in w_out])
    print("  " + safe_report[:500].replace("\n", "\n  "))


def test_update_agent_stats_increments_correctly() -> None:
    section("12 ? AgentRegistry -- update_agent_stats() logic")
    reg = AgentRegistry()
    temp_config = "test_agent_config.json"
    
    # Create initial config
    data = {
        "agents": [
            {"id": "test_agent", "name": "Test Agent", "total_jobs": 0, "successful_jobs": 0, "total_earned": 0.0, "success_rate": 0.0}
        ]
    }
    with open(temp_config, "w") as f:
        json.dump(data, f)
    
    reg.load_from_config(temp_config)
    
    # 1. Successful job
    reg.update_agent_stats("test_agent", 5.0, True)
    
    with open(temp_config, "r") as f:
        updated = json.load(f)["agents"][0]
        test("total_jobs == 1", updated["total_jobs"] == 1)
        test("successful_jobs == 1", updated["successful_jobs"] == 1)
        test("total_earned == 5.0", updated["total_earned"] == 5.0)
        test("success_rate == 100.0", updated["success_rate"] == 100.0)
    
    # 2. Failed job
    reg.update_agent_stats("test_agent", 0.0, False)
    
    with open(temp_config, "r") as f:
        updated = json.load(f)["agents"][0]
        test("total_jobs == 2", updated["total_jobs"] == 2)
        test("successful_jobs == 1", updated["successful_jobs"] == 1)
        test("success_rate == 50.0", updated["success_rate"] == 50.0)
        test("rating == 2.5", updated["rating"] == 2.5)

    if os.path.exists(temp_config): os.remove(temp_config)
    if os.path.exists(temp_config + ".lock"): os.remove(temp_config + ".lock")


def test_agent_stats_persist_after_write() -> None:
    section("13 ? AgentRegistry -- stats persistence")
    reg = AgentRegistry()
    temp_config = "test_persist.json"
    
    data = {"agents": [{"id": "p_agent", "name": "Persist Agent", "total_jobs": 10, "total_earned": 100.0}]}
    with open(temp_config, "w") as f:
        json.dump(data, f)
    
    reg.load_from_config(temp_config)
    reg.update_agent_stats("p_agent", 10.0, True)
    
    # Reload into new registry instance
    reg2 = AgentRegistry()
    reg2.load_from_config(temp_config)
    agent = reg2.get_agent_profile("p_agent")
    
    test("reloaded total_jobs == 11", agent["total_jobs"] == 11)
    test("reloaded total_earned == 110.0", agent["total_earned"] == 110.0)

    if os.path.exists(temp_config): os.remove(temp_config)


def test_concurrent_stat_updates_dont_corrupt_json() -> None:
    section("14 ? AgentRegistry -- concurrency & locking")
    import threading
    
    reg = AgentRegistry()
    temp_config = "test_concurrent.json"
    agent_id = "c_agent"
    
    data = {"agents": [{"id": agent_id, "name": "Concurrent Agent", "total_jobs": 0, "successful_jobs": 0, "total_earned": 0.0}]}
    with open(temp_config, "w") as f:
        json.dump(data, f)
    
    reg.load_from_config(temp_config)
    
    def worker():
        # Each worker adds 5 jobs
        for _ in range(5):
            reg.update_agent_stats(agent_id, 1.0, True)
            time.sleep(0.1) # Increased sleep for Windows

    threads = [threading.Thread(target=worker) for _ in range(3)]
    for t in threads: t.start()
    for t in threads: t.join()
    
    with open(temp_config, "r") as f:
        final_data = json.load(f)["agents"][0]
        # Should be 3 threads * 5 jobs = 15 total_jobs
        passed = (final_data["total_jobs"] == 15)
        test("concurrent total_jobs == 15", passed)
        test("concurrent total_earned == 15.0", final_data["total_earned"] == 15.0)
        if not passed:
            print(f"      DEBUG: Got jobs={final_data['total_jobs']}, earned={final_data['total_earned']}")

    if os.path.exists(temp_config): os.remove(temp_config)
    if os.path.exists(temp_config + ".tmp"): os.remove(temp_config + ".tmp")
    if os.path.exists(temp_config + ".lock"): os.remove(temp_config + ".lock")


# ---------------------------------------------
#  Runner
# ---------------------------------------------

def main() -> None:
    print("\n" + "=" * 60)
    print("  Syndicate - Full Test Suite")
    print("  Query under test: " + TEST_QUERY)
    print("=" * 60)

    # BaseAgent + Registry (original suite)
    test_base_agent_creation()
    test_execute_abstract()
    test_update_stats()
    test_get_stats_shape()
    test_get_card_data()
    test_agent_registry()
    test_marketplace_stats()

    # Specialist agents
    test_search_agent()
    test_analysis_agent()
    test_writing_agent()

    # End-to-end pipeline
    test_full_pipeline()

    # New Persistence & Concurrency tests (Fixes)
    test_update_agent_stats_increments_correctly()
    test_agent_stats_persist_after_write()
    test_concurrent_stat_updates_dont_corrupt_json()

    # -- Summary ------------------------------
    passed = sum(1 for _, ok in _results if ok)
    failed = sum(1 for _, ok in _results if not ok)
    total  = len(_results)

    print("\n" + "=" * 60)
    print("  Results: " + str(passed) + "/" + str(total) + " passed")
    if failed:
        print("\n   Failed tests:")
        for label, ok in _results:
            if not ok:
                print(f"    {FAIL}  {label}")
    else:
        print("   All tests passed!")
    print("=" * 60 + "\n")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
