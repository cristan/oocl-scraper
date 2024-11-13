import json


class Spider:
    def __init__(self, input_filename, output_filename):
        self.input_filename = input_filename
        self.output_filename = output_filename

    def read_data(self):
        with open(self.input_filename, mode='r', encoding='utf-8') as f:
            return [item for item in json.load(f) if item.get('status') == 'INITIAL']

    def write_data(self, data):
        with open(self.input_filename, mode='w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def update_status(self, index, status, data):
        data[index]['status'] = status
        self.write_data(data)

    def delete_object(self, index, data):
        del data[index]
        self.write_data(data)

    def write_output(self, data):
        try:
            with open(self.output_filename, 'r', encoding='utf-8') as file:
                existing_data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = []

        existing_data.append(data)
        with open(self.output_filename, 'w', encoding='utf-8') as file:
            json.dump(existing_data, file, indent=4, ensure_ascii=False)
