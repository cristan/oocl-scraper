import json
import logging

logger = logging.getLogger(__name__)


class Spider:
    def __init__(self, input_filename, output_filename):
        self.input_filename = input_filename
        self.output_filename = output_filename
        logger.info(f"Spider initialized with input: {input_filename} and output: {output_filename}")

    def read_data(self):
        try:
            with open(self.input_filename, mode='r', encoding='utf-8') as f:
                data = [item for item in json.load(f) if item.get('status') == 'INITIAL']
                logger.info(f"Read {len(data)} initial items from {self.input_filename}")
                return data
        except Exception as e:
            logger.error(f"Failed to read data from {self.input_filename}: {e}")
            raise

    def write_data(self, data):
        try:
            with open(self.input_filename, mode='w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
                logger.info(f"Successfully wrote data to {self.input_filename}")
        except Exception as e:
            logger.error(f"Failed to write data to {self.input_filename}: {e}")
            raise

    def update_status(self, index, status, data):
        try:
            data[index]['status'] = status
            self.write_data(data)
            logger.info(f"Updated status of item at index {index} to {status}")
        except Exception as e:
            logger.error(f"Failed to update status of item at index {index}: {e}")
            raise

    def delete_object(self, index, data):
        try:
            del data[index]
            self.write_data(data)
            logger.info(f"Deleted item at index {index} from data")
        except Exception as e:
            logger.error(f"Failed to delete item at index {index}: {e}")
            raise

    def write_output(self, data):
        try:
            try:
                with open(self.output_filename, 'r', encoding='utf-8') as file:
                    existing_data = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_data = []

            existing_data.append(data)
            with open(self.output_filename, 'w', encoding='utf-8') as file:
                json.dump(existing_data, file, indent=4, ensure_ascii=False)
                logger.info(f"Appended data to {self.output_filename}")
        except Exception as e:
            logger.error(f"Failed to write output to {self.output_filename}: {e}")
            raise