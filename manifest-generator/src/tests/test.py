import json
import unittest
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class TestManifestComparison(unittest.TestCase):
    def setUp(self):
        self.current_dir = Path(__file__).parent
        
        with open(self.current_dir / "generated.json") as f:
            self.generated = json.load(f)
            
        with open(self.current_dir / "existing.json") as f:
            self.existing = json.load(f)
        
        logger.info("Files loaded successfully")

    def test_spec_structure(self):
        # Compare input schemas
        generated_input = self.generated["spec"]["input"]
        existing_input = self.existing["specs"]["input"]
        
        logger.info("\nComparing input properties:")
        logger.info(f"Generated input properties: {sorted(generated_input['properties'].keys())}")
        logger.info(f"Existing input properties: {sorted(existing_input['properties'].keys())}")
        
        # Check input properties match
        self.assertEqual(
            set(generated_input["properties"].keys()),
            set(existing_input["properties"].keys()),
            "Input properties don't match"
        )

        # Compare output schemas
        generated_output = self.generated["spec"]["output"]
        existing_output = self.existing["specs"]["output"]
        
        logger.info("\nComparing output properties:")
        logger.info(f"Generated output properties: {sorted(generated_output['properties'].keys())}")
        logger.info(f"Existing output properties: {sorted(existing_output['properties'].keys())}")
        
        # Check output properties match
        self.assertEqual(
            set(generated_output["properties"].keys()),
            set(existing_output["properties"].keys()),
            "Output properties don't match"
        )

        # Compare config schemas
        generated_config = self.generated["spec"]["config"]
        existing_config = self.existing["specs"]["config"]
        
        logger.info("\nComparing config properties:")
        logger.info(f"Generated config properties: {sorted(generated_config['properties'].keys())}")
        logger.info(f"Existing config properties: {sorted(existing_config['properties'].keys())}")
        
        # Check config properties match
        self.assertEqual(
            set(generated_config["properties"].keys()),
            set(existing_config["properties"].keys()),
            "Config properties don't match"
        )

if __name__ == '__main__':
    unittest.main()