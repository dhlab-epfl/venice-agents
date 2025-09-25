# LLM Agents for Interactive Exploration of Historical Cadastre Data: Framework and Application to Venice

This repository contains the implementation for the research paper: **LLM Agents for Interactive Exploration of Historical Cadastre Data: Framework and Application to Venice** ([arXiv:2505.17148](https://arxiv.org/abs/2505.17148)) published in **Computational Humanities Research**.

This research explores Venice's urban history during the critical period from 1740 to 1808, capturing the transition following the fall of the ancient Republic and the Ancien Régime. The work addresses the challenges of processing complex, non-standardized cadastral data through two complementary approaches:

1. **SQL Agent**: For handling structured queries about specific cadastral information
2. **Coding Agents**: For complex analytical operations requiring custom data manipulation

## Methodology

Our framework implements a text-to-programs approach that leverages Large Language Models (LLMs) to translate natural language queries into executable code for processing historical cadastral records. The system is designed to:

- Bridge past and present urban landscapes through spatial queries
- Handle diverse formats and human annotations in historical data
- Generate verifiable program outputs to minimize hallucination
- Enable reconstruction of past population information, property features, and spatiotemporal comparisons

## Repository Structure

📁 [sql_agent](sql_agent/) - Contains the SQL Agent implementation for structured queries.

📁 [coding_agents](coding_agents/) - Contains the Coding Agents implementation for open-ended questions.

## Citation

If you use this work in your research, please cite:

```bibtex
@article{karch2025llm,
  title={LLM-Powered Agents for Navigating Venice's Historical Cadastre},
  author={Tristan Karch and Jakhongir Saydaliev and Isabella Di Lenardo and Frédéric Kaplan},
  journal={arXiv preprint arXiv:2505.17148},
  year={2025}
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.