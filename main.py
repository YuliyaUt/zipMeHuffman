def get_filename_without_extension(filename):
    if len(filename) == 0:
        return ""
    li = filename.split(".")
    li.pop()
    return ".".join(li)


def count_bytes_occurrences(filename):
    occurrences = [0] * 256
    total_count = 0
    with open(filename, "br") as f:
        b = f.read(1)
        while b:
            occurrences[ord(b)] += 1
            total_count += 1
            b = f.read(1)
    f.close()
    return total_count, occurrences


def create_count_to_char_map(occurrences):
    chr_to_count_map = {i: occurrences[i] for i in range(256)}
    count_to_chr_map = {value: [] for value in sorted(chr_to_count_map.values())}
    if 0 in count_to_chr_map.keys():
        count_to_chr_map.pop(0)
    for i in range(256):
        if occurrences[i] != 0:
            count_to_chr_map[occurrences[i]].append(i)
    return count_to_chr_map


def build_codes_array(total_count, model_map):
    codes_array = [""] * 256
    while total_count not in list(model_map.keys()):
        first_min_frequency = sorted(model_map.keys())[0]
        second_minimal_frequency = first_min_frequency
        all_rarest_chars = model_map[first_min_frequency]
        if len(all_rarest_chars) == 0:
            model_map.pop(first_min_frequency)
            continue
        first_rarest_char_set = all_rarest_chars.pop()
        if len(all_rarest_chars) != 0:
            second_rarest_char_set = all_rarest_chars.pop()
            model_map[first_min_frequency] = all_rarest_chars
        else:
            model_map.pop(first_min_frequency)
            second_minimal_frequency = sorted(model_map.keys())[0]
            all_rarest_chars = model_map[second_minimal_frequency]
            second_rarest_char_set = all_rarest_chars.pop()
            if len(all_rarest_chars) == 0:
                model_map.pop(second_minimal_frequency)
            else:
                model_map[second_minimal_frequency] = all_rarest_chars
        merged_list = []
        if type(first_rarest_char_set) is list:
            for i in list(first_rarest_char_set):
                codes_array[i] = "0" + codes_array[i]
                merged_list.append(i)
        else:
            codes_array[first_rarest_char_set] = "0" + codes_array[first_rarest_char_set]
            merged_list.append(first_rarest_char_set)
        if type(second_rarest_char_set) is list:
            for i in list(second_rarest_char_set):
                codes_array[i] = "1" + codes_array[i]
                merged_list.append(i)
        else:
            codes_array[second_rarest_char_set] = "1" + codes_array[second_rarest_char_set]
            merged_list.append(second_rarest_char_set)
        if (first_min_frequency + second_minimal_frequency) in list(model_map.keys()):
            model_map[first_min_frequency + second_minimal_frequency].append(merged_list)
        else:
            model_map[first_min_frequency + second_minimal_frequency] = [merged_list]
    return codes_array


def write_code_to_file(output_file, codes_array):
    for i in range(256):
        output_file.write(i.to_bytes(1, "big"))
        output_file.write(len(codes_array[i]).to_bytes(1, "big"))
        if codes_array[i] != "":
            output_file.write(bytes(codes_array[i], "utf-8"))
    output_file.write(bytes("\n", "utf-8"))
    pass


def write_encoded_data_to_file(input_file, output_file, codes_array):
    b = input_file.read(1)
    old_code = ""
    while b:
        code = old_code + codes_array[ord(b)]
        end_index = (len(code) // 8) * 8
        old_code = code[end_index:]
        for i in range(0, end_index // 8):
            curr_str = code[i * 8:i * 8 + 8]
            curr_int = int(curr_str, 2)
            c = curr_int.to_bytes(1, "big")
            output_file.write(c)
        b = input_file.read(1)
    rem = len(old_code)
    code = old_code + "0" * (8 - len(old_code))
    output_file.write(int(code, 2).to_bytes(1, "big"))
    output_file.write(rem.to_bytes(1, "big"))
    pass


def first_mode(filename):
    param = 1
    # Step 1: count statistics to build optimal code
    total_count, occurrences = count_bytes_occurrences(filename)
    count_to_chr_map = create_count_to_char_map(occurrences)
    print(count_to_chr_map)
    model_map = count_to_chr_map.copy()
    codes_array = build_codes_array(total_count, model_map)
    print({i: codes_array[i] for i in range(256)})
    # Step 2: encoding file
    with open(".".join([filename, "zmh"]), "wb") as output_file:
        write_code_to_file(output_file, codes_array)
        output_file.write(bytes("BEGIN", "utf-8"))
        with open(filename, "rb") as input_file:
            write_encoded_data_to_file(input_file, output_file, codes_array)
        output_file.write(bytes("END", "utf-8"))
        input_file.close()
        output_file.close()


def decode(output_file, codes_dict, c):
    word = ""
    i = 0
    while i < len(c):
        word += c[i]
        if word in codes_dict.keys():
            output_file.write(codes_dict[word].to_bytes(1, "big"))
            word = ""
        i += 1
    return word


def read_code_from_file(input_file):
    inv_codes = {}
    b = input_file.read(1)
    for i in range(256):
        j = ord(b)
        length = ord(input_file.read(1))
        if length > 0:
            codeword = "".join(map(chr, input_file.read(length)))
            inv_codes.setdefault(codeword, j)
        b = input_file.read(1)
    return inv_codes


def check_begin(input_file):
    bytes_message = bytearray(input_file.read(5))
    message = "".join(map(chr, bytes_message))
    if message != "BEGIN":
        print("Invalid format!")
        return -1
    return 0


def get_binary_string(c):
    bin_str = (str(bin(c))[2:])
    bin_str = "0" * (8 - len(bin_str)) + bin_str
    return bin_str


def left_shift_byte_array(bytes_message, b):
    for i in range(0, len(bytes_message)-1):
        bytes_message[i] = bytes_message[i + 1]
    bytes_message[len(bytes_message)-1] = ord(b)
    return bytes_message


def second_mode(filename):
    extension = filename.split(".").pop()
    assert extension == "zmh"
    with open(filename, "rb") as input_file:
        with open("r_" + get_filename_without_extension(filename), "wb") as output_file:
            inv_codes = read_code_from_file(input_file)
            print(inv_codes)
            if check_begin(input_file) != 0:
                input_file.close()
                output_file.close()
                return -1
            bytes_message = []
            for i in range(0, 5):
                bytes_message.append(ord(input_file.read(1)))
            message = "".join(map(chr, bytes_message))
            b = input_file.read(1)
            rem = ""
            while b:
                rem = rem + get_binary_string(bytes_message[0])
                rem = decode(output_file, inv_codes, rem)
                bytes_message = left_shift_byte_array(bytes_message, b)
                message = message[1:len(message)] + "".join(map(chr, b))
                b = input_file.read(1)
            last = get_binary_string(bytes_message[0])
            last = rem + last[0:bytes_message[1]]
            decode(output_file, inv_codes, last)
            if message[2:len(message)] != "END":
                print("Incorrect format")
            input_file.close()
            output_file.close()


def main():
    print("Enter filename:")
    filename = input()
    print(filename)
    # filename = "zay.docx"
    print("To convert to .zmh enter 1, to convert from .zmh enter 2")
    opt = int(input())
    if opt == 1:
        first_mode(filename)
    elif opt == 2:
        second_mode(filename)
    else:
        print("Try again")


if __name__ == "__main__":
    main()

