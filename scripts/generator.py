import argparse, csv, math, random

def main():
    parser = argparse.ArgumentParser(description="Generate random geographic points within a bounding box.")
    parser.add_argument("--n", type=int, required=True, help="Number of points to generate.")
    parser.add_argument("--center-lat", type=float, required=True, help="Designated center latitude ")
    parser.add_argument("--center-lon", type=float, required=True, help="Designated center longitude ")
    parser.add_argument("--std-km", type=float, required=True, help="Standard deviation in kilometers.")
    parser.add_argument("--output-file", type=str, required=True, help="Output CSV file to save the generated points.")
    parser.add_argument("--seed", type=int, required=False, default=None, help="Random seed for reproducibility.")

    args = parser.parse_args()


    with open(args.output_file, mode='w', newline='') as csvfile:
        fieldnames = ['lat', 'lon']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for _ in range(args.n):
            lat, lon = generate_random_point(
                args.center_lat,
                args.center_lon,
                args.std_km,  # Approx conversion from km to degrees
                args.seed
            )
            writer.writerow({'lat': lat, 'lon': lon})
    
def generate_random_point(center_lat, center_lon, std_km, seed=None)-> tuple:
    mlat = 111320  
    mlon = mlat * math.cos(math.radians(center_lat))
    if seed is not None:
        random.seed(seed)
    
    center_m = center_lat * mlat
    center_n = center_lon * mlon

    lat = random.gauss(center_m, std_km) / mlat
    lon = random.gauss(center_n, std_km) /mlon

    return lat, lon

if __name__ == "__main__":
    main()

# Example usage:
# python scripts/generator.py --n 100000 --center-lat 51.5074 --center-lon -0.1278 --std-km 5 --out tmp/points_100k.csv --seed 42
