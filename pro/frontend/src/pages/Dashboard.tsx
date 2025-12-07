import {
    Card,
    CardHeader,
    CardTitle,
    CardContent,
  } from "@/components/ui/card";
  import { Badge } from "@/components/ui/badge";
  
  export default function Dashboard() {
    return (
      <div className="flex flex-col gap-8">
  
        <h2 className="text-3xl font-bold">Dashboard</h2>
  
        {/* SUMMARY CARDS */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
  
          <Card className="shadow-sm hover:shadow-md transition">
            <CardHeader>
              <CardTitle>Weekly Mileage</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-primary">42.3 mi</p>
              <Badge className="mt-2 bg-primary/15 text-primary">Up 12%</Badge>
            </CardContent>
          </Card>
  
          <Card className="shadow-sm hover:shadow-md transition">
            <CardHeader>
              <CardTitle>Average Pace</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-primary">7:32 /mi</p>
              <Badge className="mt-2">Consistent</Badge>
            </CardContent>
          </Card>
  
          <Card className="shadow-sm hover:shadow-md transition">
            <CardHeader>
              <CardTitle>Training Load</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-primary">Moderate</p>
              <Badge className="mt-2 bg-yellow-200 text-yellow-800">Balanced</Badge>
            </CardContent>
          </Card>
  
        </div>
      </div>
    );
  }
  