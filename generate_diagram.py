#!/usr/bin/env python3
"""
Animated EKS architecture PDF — traffic flow shown as animated dots
using PDF annotation JavaScript + multiple pages blended as frames.
Uses ReportLab for drawing + manual PDF object injection for JS animation.
"""
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib import colors
import math, io

W, H = landscape(A3)
OUT = "/Users/SanjayAku/eks-cluster/architecture.pdf"

C = {
    "bg":"#0D1117","panel":"#161B22","border":"#30363D",
    "purple":"#8B5CF6","purple_l":"#C4B5FD",
    "blue":"#3B82F6","blue_l":"#BFDBFE",
    "green":"#10B981","green_l":"#A7F3D0",
    "orange":"#F59E0B","orange_l":"#FDE68A",
    "red":"#EF4444","red_l":"#FECACA",
    "teal":"#06B6D4","teal_l":"#A5F3FC",
    "pink":"#EC4899","pink_l":"#FBCFE8",
    "white":"#F0F6FC","muted":"#8B949E","card":"#1C2128",
}

def hex2rgb(h):
    h=h.lstrip("#"); return tuple(int(h[i:i+2],16)/255 for i in (0,2,4))
def col(h): return colors.Color(*hex2rgb(h))

def grad(cv,x,y,w,h,c1,c2,steps=30):
    r1,g1,b1=hex2rgb(c1); r2,g2,b2=hex2rgb(c2); sh=h/steps
    for i in range(steps):
        t=i/steps
        cv.setFillColor(colors.Color(r1+(r2-r1)*t,g1+(g2-g1)*t,b1+(b2-b1)*t))
        cv.rect(x,y+i*sh,w,sh+0.5,fill=1,stroke=0)

def glow(cv,x,y,w,h,gc,r=8,s=4):
    rr,gg,bb=hex2rgb(gc)
    for i in range(s,0,-1):
        a=0.07*i; pad=(s-i+1)*2
        cv.setFillColor(colors.Color(rr,gg,bb,alpha=a))
        cv.setStrokeColor(colors.Color(rr,gg,bb,alpha=0))
        cv.roundRect(x-pad,y-pad,w+pad*2,h+pad*2,r+pad,fill=1,stroke=0)

def card(cv,x,y,w,h,bc,title=None,tc=None,r=10):
    glow(cv,x,y,w,h,bc)
    cv.setFillColor(col(C["card"])); cv.setStrokeColor(col(bc)); cv.setLineWidth(1.5)
    cv.roundRect(x,y,w,h,r,fill=1,stroke=1)
    if title:
        cv.setFillColor(col(tc or bc)); cv.setFont("Helvetica-Bold",8)
        cv.drawString(x+10,y+h-13,title)
        cv.setStrokeColor(col(bc)); cv.setLineWidth(0.5)
        cv.line(x+8,y+h-16,x+w-8,y+h-16)

def badge(cv,x,y,w,h,bg,bc,text,tc=None,fs=7.5):
    glow(cv,x,y,w,h,bc,r=6,s=3)
    cv.setFillColor(col(bg)); cv.setStrokeColor(col(bc)); cv.setLineWidth(1.2)
    cv.roundRect(x,y,w,h,6,fill=1,stroke=1)
    cv.setFillColor(col(tc or bc)); cv.setFont("Helvetica-Bold",fs)
    cv.drawCentredString(x+w/2,y+h/2-fs/2.8,text)

def ptag(cv,x,y,text,bc):
    tw=len(text)*4.8+10
    cv.setFillColor(col(C["card"])); cv.setStrokeColor(col(bc)); cv.setLineWidth(0.6)
    cv.roundRect(x,y,tw,11,3,fill=1,stroke=1)
    cv.setFillColor(col(C["white"])); cv.setFont("Helvetica",6)
    cv.drawString(x+4,y+2.5,text); return tw+4

def arrow(cv,x1,y1,x2,y2,color,dashed=False,label=None,lw=1.5):
    cv.setStrokeColor(col(color)); cv.setLineWidth(lw)
    cv.setDash(5,3) if dashed else cv.setDash()
    cv.line(x1,y1,x2,y2); cv.setDash()
    ang=math.atan2(y2-y1,x2-x1); al=8; aa=0.4
    cv.setFillColor(col(color))
    p=cv.beginPath(); p.moveTo(x2,y2)
    p.lineTo(x2-al*math.cos(ang-aa),y2-al*math.sin(ang-aa))
    p.lineTo(x2-al*math.cos(ang+aa),y2-al*math.sin(ang+aa))
    p.close(); cv.drawPath(p,fill=1,stroke=0)
    if label:
        cv.setFillColor(col(C["muted"])); cv.setFont("Helvetica-Oblique",6)
        cv.drawCentredString((x1+x2)/2+6,(y1+y2)/2+5,label)

def dots_bg(cv,color,sp=22):
    cv.setFillColor(col(color))
    for xi in range(0,int(W),sp):
        for yi in range(0,int(H),sp):
            cv.circle(xi,yi,0.6,fill=1,stroke=0)

# ── Traffic dot along a path ─────────────────────────────────────────────────
def traffic_dot(cv, x, y, color, size=5, label=None):
    """Draw a glowing traffic packet dot."""
    r,g,b = hex2rgb(color)
    for i in range(3,0,-1):
        cv.setFillColor(colors.Color(r,g,b,alpha=0.15*i))
        cv.circle(x,y,size+i*2,fill=1,stroke=0)
    cv.setFillColor(col(color))
    cv.circle(x,y,size,fill=1,stroke=0)
    cv.setFillColor(colors.white)
    cv.circle(x,y,size*0.35,fill=1,stroke=0)
    if label:
        cv.setFillColor(col(color)); cv.setFont("Helvetica-Bold",6)
        cv.drawCentredString(x,y-size-5,label)

def animated_path(cv, points, color, n_dots=4, frame=0, total_frames=12):
    """Draw n_dots evenly spaced along a polyline, offset by frame."""
    # build cumulative distances
    segs = []
    total = 0
    for i in range(len(points)-1):
        x1,y1=points[i]; x2,y2=points[i+1]
        d=math.hypot(x2-x1,y2-y1); segs.append((x1,y1,x2,y2,d)); total+=d
    if total==0: return
    for di in range(n_dots):
        t = ((di/n_dots) + (frame/total_frames)) % 1.0
        dist = t * total
        acc = 0
        for x1,y1,x2,y2,d in segs:
            if acc+d >= dist:
                frac = (dist-acc)/d if d>0 else 0
                px = x1+(x2-x1)*frac; py = y1+(y2-y1)*frac
                traffic_dot(cv,px,py,color,size=4)
                break
            acc+=d

# ── Layout constants (shared across frames) ──────────────────────────────────
def layout():
    vx,vy,vw,vh = 20,18,W-40,H-165
    left_w = 88; right_w = 128; az_gap = 11
    az_total = vw - left_w - right_w - 5*az_gap
    az_w = az_total / 3
    az1_x = vx+left_w+2*az_gap
    az2_x = az1_x+az_w+az_gap
    az3_x = az2_x+az_w+az_gap
    az_y = vy+14; az_h = vh-52
    pub_h=58; pub_w=az_w-18; pub_y=az_y+az_h-pub_h-10
    priv_h=az_h-pub_h-44; priv_y=az_y+20; priv_w=az_w-18
    rp_x=az3_x+az_w+az_gap; rp_w=vx+vw-rp_x-12
    sg_x=vx+12; sg_y=vy+12; sg_w=az1_x-vx-az_gap-12; sg_h=az_h-8
    inet_y=H-95; alb_x=W/2+90; r53_x=W/2-230; igw_x=W/2-65; igw_y=H-138
    return dict(vx=vx,vy=vy,vw=vw,vh=vh,
                az1_x=az1_x,az2_x=az2_x,az3_x=az3_x,
                az_y=az_y,az_h=az_h,az_w=az_w,
                pub_h=pub_h,pub_w=pub_w,pub_y=pub_y,
                priv_h=priv_h,priv_y=priv_y,priv_w=priv_w,
                rp_x=rp_x,rp_w=rp_w,
                sg_x=sg_x,sg_y=sg_y,sg_w=sg_w,sg_h=sg_h,
                inet_y=inet_y,alb_x=alb_x,r53_x=r53_x,
                igw_x=igw_x,igw_y=igw_y)

def draw_base(cv, L):
    vx,vy,vw,vh=L["vx"],L["vy"],L["vw"],L["vh"]
    az1_x,az2_x,az3_x=L["az1_x"],L["az2_x"],L["az3_x"]
    az_y,az_h,az_w=L["az_y"],L["az_h"],L["az_w"]
    pub_h,pub_w,pub_y=L["pub_h"],L["pub_w"],L["pub_y"]
    priv_h,priv_y,priv_w=L["priv_h"],L["priv_y"],L["priv_w"]
    rp_x,rp_w=L["rp_x"],L["rp_w"]
    sg_x,sg_y,sg_w,sg_h=L["sg_x"],L["sg_y"],L["sg_w"],L["sg_h"]
    inet_y,alb_x,r53_x=L["inet_y"],L["alb_x"],L["r53_x"]
    igw_x,igw_y=L["igw_x"],L["igw_y"]

    # Background
    grad(cv,0,0,W,H,"#0D1117","#111827")
    dots_bg(cv,"#1F2937")

    # Header
    grad(cv,0,H-52,W,52,"#1E1B4B","#0D1117")
    cv.setFillColor(col(C["purple_l"])); cv.setFont("Helvetica-Bold",20)
    cv.drawCentredString(W/2,H-34,"Amazon EKS Cluster — AWS Architecture (3-AZ)")
    cv.setFillColor(col(C["muted"])); cv.setFont("Helvetica",9)
    cv.drawCentredString(W/2,H-46,"Terraform Package  ·  networking · iam · eks · alb · dns · cleanup · s3 · s3-backend")

    # Top row
    badge(cv,W/2-55,inet_y,110,26,"#0C1A2E",C["blue"],"🌐  Internet",C["blue_l"],fs=9)
    badge(cv,r53_x,inet_y,130,26,"#1A0A2E",C["purple"],"🔷  Route 53",C["purple_l"],fs=8)
    cv.setFillColor(col(C["muted"])); cv.setFont("Helvetica",6.5)
    cv.drawCentredString(r53_x+65,inet_y-9,"example.com / www → ALB alias")
    badge(cv,alb_x,inet_y,160,26,"#0A1A0A",C["green"],"⚖  Application Load Balancer",C["green_l"],fs=8)
    cv.setFillColor(col(C["muted"])); cv.setFont("Helvetica",6.5)
    cv.drawCentredString(alb_x+80,inet_y-9,":80 redirect → :443  |  :443 HTTPS forward")
    badge(cv,igw_x,igw_y,130,24,"#0C2A1A",C["green"],"⇅  Internet Gateway",C["green_l"],fs=8)

    # Static arrows (structure)
    arrow(cv,r53_x+130,inet_y+13,alb_x,inet_y+13,C["purple"],label="alias record")
    arrow(cv,W/2+55,inet_y+13,alb_x,inet_y+13,C["blue"],label="HTTPS :443")
    arrow(cv,W/2,inet_y,W/2,igw_y+24,C["blue"])

    # VPC
    glow(cv,vx,vy,vw,vh,C["purple"],r=14,s=5)
    cv.setFillColor(colors.Color(*hex2rgb(C["panel"]),alpha=0.85))
    cv.setStrokeColor(col(C["purple"])); cv.setLineWidth(2)
    cv.roundRect(vx,vy,vw,vh,14,fill=1,stroke=1)
    cv.setFillColor(col(C["purple"])); cv.setFont("Helvetica-Bold",10)
    cv.drawString(vx+14,vy+vh-16,"VPC  —  10.1.0.0/16")
    cv.setFillColor(col(C["muted"])); cv.setFont("Helvetica",8)
    cv.drawString(vx+14,vy+vh-27,"module: networking  ·  3 AZs  ·  3 NAT Gateways")

    # AZ containers
    az_labels=["us-east-1a","us-east-1b","us-east-1c"]
    for ax,lbl in zip([az1_x,az2_x,az3_x],az_labels):
        glow(cv,ax,az_y,az_w,az_h,C["blue"],r=10,s=3)
        cv.setFillColor(colors.Color(*hex2rgb("#0D1F35"),alpha=0.7))
        cv.setStrokeColor(col(C["blue"])); cv.setLineWidth(1.2); cv.setDash(6,3)
        cv.roundRect(ax,az_y,az_w,az_h,10,fill=1,stroke=1); cv.setDash()
        cv.setFillColor(col(C["blue"])); cv.setFont("Helvetica-Bold",7.5)
        cv.drawString(ax+8,az_y+az_h-13,f"AZ  {lbl}")

    # Public subnets + NAT
    cidrs_pub=["10.1.1.0/24","10.1.2.0/24","10.1.3.0/24"]
    nat_centers=[]
    for ax,cidr in zip([az1_x,az2_x,az3_x],cidrs_pub):
        px=ax+9
        card(cv,px,pub_y,pub_w,pub_h,C["green"],title=f"Public  {cidr}",tc=C["green_l"])
        badge(cv,px+8,pub_y+10,pub_w-16,22,"#0C2A1A",C["green"],"⇅  NAT Gateway",C["green_l"],fs=7)
        nat_centers.append((px+pub_w/2, pub_y+10+11))

    # IGW → each NAT
    for ncx,ncy in nat_centers:
        arrow(cv,igw_x+65,igw_y+12,ncx,ncy+11,C["green"])

    # Private subnets
    cidrs_priv=["10.1.11.0/24","10.1.12.0/24","10.1.13.0/24"]
    node_centers=[]
    for ax,cidr in zip([az1_x,az2_x,az3_x],cidrs_priv):
        px=ax+9
        card(cv,px,priv_y,priv_w,priv_h,C["orange"],title=f"Private  {cidr}",tc=C["orange_l"])
        ng_w=(priv_w-24)/2
        for ni,ng in enumerate(["general-ng","spot-ng"]):
            nx=px+8+ni*(ng_w+8); ny=priv_y+14; nh=priv_h-26
            card(cv,nx,ny,ng_w,nh,C["orange"],title=ng,tc=C["orange_l"],r=7)
            for ei in range(2):
                badge(cv,nx+5,ny+nh-26-ei*28,ng_w-10,20,"#1A1200",C["orange"],"EC2",C["orange_l"],fs=7)
        node_centers.append((px+priv_w/2, priv_y+priv_h/2))

    # NAT → private (outbound)
    for (ncx,ncy),(nodex,nodey) in zip(nat_centers,node_centers):
        arrow(cv,ncx,ncy,nodex,nodey+priv_h//2,C["green"],dashed=True)

    # Right panels
    eks_h=72; eks_y=az_y+az_h-eks_h-10
    card(cv,rp_x,eks_y,rp_w,eks_h,C["purple"],title="EKS Control Plane",tc=C["purple_l"])
    cv.setFillColor(col(C["muted"])); cv.setFont("Helvetica",7)
    cv.drawCentredString(rp_x+rp_w/2,eks_y+eks_h-26,"(AWS Managed)")
    badge(cv,rp_x+6,eks_y+8,rp_w-12,20,"#1A0A2E",C["purple"],"API · etcd · Scheduler  |  k8s v1.31",C["purple_l"],fs=7)
    cv.setFillColor(col(C["purple_l"])); cv.setFont("Helvetica-Bold",8)
    cv.drawCentredString(rp_x+rp_w/2,eks_y+eks_h-38,"3-AZ  High Availability")
    for ax in [az1_x,az2_x,az3_x]:
        arrow(cv,rp_x,eks_y+eks_h/2,ax+9+priv_w,priv_y+priv_h/2,C["purple"])

    iam_h=priv_h-eks_h-18; iam_y=priv_y
    card(cv,rp_x,iam_y,rp_w,iam_h,C["red"],title="IAM Roles",tc=C["red_l"])
    roles=[("cluster-role",C["purple_l"],["AmazonEKSClusterPolicy","AmazonEKSServicePolicy"]),
           ("nodegroup-role",C["orange_l"],["AmazonEKSWorkerNodePolicy","AmazonEKS_CNI_Policy","AmazonEC2ContainerRegistryReadOnly"])]
    ry=iam_y+iam_h-22
    for rname,rc,pols in roles:
        cv.setFillColor(col(rc)); cv.setFont("Helvetica-Bold",7.5)
        cv.drawString(rp_x+8,ry,rname); ry-=12
        px_off=rp_x+10
        for pol in pols:
            tw=ptag(cv,px_off,ry-2,pol,C["purple"]); px_off+=tw
            if px_off>rp_x+rp_w-10: px_off=rp_x+10; ry-=13
        ry-=14
    arrow(cv,rp_x+rp_w/2,iam_y+iam_h,rp_x+rp_w/2,eks_y,C["red"],dashed=True,label="assumes role")

    s3_h=pub_h-4; s3_y=pub_y
    card(cv,rp_x,s3_y,rp_w,s3_h,C["teal"],title="S3 — Terraform State",tc=C["teal_l"])
    badge(cv,rp_x+6,s3_y+8,rp_w-12,18,"#001A1A",C["teal"],"Versioned · AES-256 · No Public Access",C["teal_l"],fs=6.5)
    arrow(cv,rp_x,s3_y+s3_h/2,az3_x+az_w,eks_y+eks_h/2,C["teal"],dashed=True,label="remote state")

    # SG panel
    card(cv,sg_x,sg_y,sg_w,sg_h,C["red"],title="Security Groups",tc=C["red_l"])
    sg_items=[("alb-sg",C["green_l"],[":80/:443 ← 0.0.0.0/0","all → 0.0.0.0/0"]),
              ("cluster-sg",C["purple_l"],[":443 ← nodes",":443 ← admin"]),
              ("nodes-sg",C["orange_l"],["NodePort ← alb","all ← cluster","all ← self"])]
    ry2=sg_y+sg_h-22
    for sgn,sgc,rules in sg_items:
        cv.setFillColor(col(sgc)); cv.setFont("Helvetica-Bold",7)
        cv.drawString(sg_x+6,ry2,sgn); ry2-=10
        for r in rules:
            cv.setFillColor(col(C["muted"])); cv.setFont("Helvetica",6.5)
            cv.drawString(sg_x+10,ry2,f"• {r}"); ry2-=9
        ry2-=5

    # Legend
    items=[(C["purple"],False,"Control plane ↔ nodes"),(C["green"],True,"NAT / ALB traffic"),
           (C["red"],True,"IAM trust"),(C["teal"],True,"Terraform state"),(C["blue"],False,"Internet traffic")]
    lx=vx+vw-175; ly=vy+10
    cv.setFillColor(colors.Color(*hex2rgb(C["card"]),alpha=0.9))
    cv.setStrokeColor(col(C["border"])); cv.setLineWidth(0.8)
    cv.roundRect(lx,ly,165,14*len(items)+14,6,fill=1,stroke=1)
    cv.setFillColor(col(C["white"])); cv.setFont("Helvetica-Bold",7.5)
    cv.drawString(lx+8,ly+14*len(items)+4,"Legend")
    for i,(lc,dashed,ltxt) in enumerate(items):
        y=ly+10+i*14
        cv.setStrokeColor(col(lc)); cv.setLineWidth(1.5)
        cv.setDash(4,3) if dashed else cv.setDash()
        cv.line(lx+8,y+4,lx+36,y+4); cv.setDash()
        cv.setFillColor(col(C["white"])); cv.setFont("Helvetica",7)
        cv.drawString(lx+42,y+1,ltxt)

    return nat_centers, node_centers, eks_y, eks_h

def draw_traffic(cv, L, frame, total, nat_centers, node_centers, eks_y, eks_h):
    """Overlay animated traffic dots for this frame."""
    inet_y,alb_x,r53_x=L["inet_y"],L["alb_x"],L["r53_x"]
    igw_x,igw_y=L["igw_x"],L["igw_y"]
    rp_x,rp_w=L["rp_x"],L["rp_w"]
    priv_y,priv_h=L["priv_y"],L["priv_h"]
    az1_x,az2_x,az3_x=L["az1_x"],L["az2_x"],L["az3_x"]
    priv_w=L["priv_w"]

    # Path 1: Internet → Route53 → ALB
    p1=[(W/2,inet_y+13),(r53_x+130,inet_y+13),(alb_x,inet_y+13)]
    animated_path(cv,p1,C["blue"],n_dots=3,frame=frame,total_frames=total)

    # Path 2: ALB → IGW → NAT AZ1 → nodes AZ1
    ncx1,ncy1=nat_centers[0]; nx1,ny1=node_centers[0]
    p2=[(alb_x,inet_y+13),(W/2+55,inet_y+13),(W/2,inet_y),(W/2,igw_y+24),
        (igw_x+65,igw_y+12),(ncx1,ncy1+11),(nx1,ny1)]
    animated_path(cv,p2,C["green"],n_dots=4,frame=frame,total_frames=total)

    # Path 3: ALB → NAT AZ2 → nodes AZ2
    ncx2,ncy2=nat_centers[1]; nx2,ny2=node_centers[1]
    p3=[(alb_x+80,inet_y),(alb_x+80,inet_y-20),(ncx2,ncy2+11),(nx2,ny2)]
    animated_path(cv,p3,C["green"],n_dots=3,frame=frame+4,total_frames=total)

    # Path 4: ALB → NAT AZ3 → nodes AZ3
    ncx3,ncy3=nat_centers[2]; nx3,ny3=node_centers[2]
    p4=[(alb_x+120,inet_y),(alb_x+120,inet_y-30),(ncx3,ncy3+11),(nx3,ny3)]
    animated_path(cv,p4,C["green"],n_dots=3,frame=frame+8,total_frames=total)

    # Path 5: EKS control plane ↔ nodes (purple)
    for ax,nc in zip([az1_x,az2_x,az3_x],node_centers):
        p5=[(rp_x,eks_y+eks_h/2),(ax+9+priv_w,priv_y+priv_h/2)]
        animated_path(cv,p5,C["purple"],n_dots=2,frame=frame+2,total_frames=total)

    # Frame counter badge
    cv.setFillColor(colors.Color(*hex2rgb(C["card"]),alpha=0.8))
    cv.roundRect(W-80,10,70,18,4,fill=1,stroke=0)
    cv.setFillColor(col(C["muted"])); cv.setFont("Helvetica",7)
    cv.drawCentredString(W-45,16,f"frame {frame+1}/{total}  ▶ traffic flow")

# ── Generate N frames as pages ────────────────────────────────────────────────
FRAMES = 12
cv = canvas.Canvas(OUT, pagesize=landscape(A3))
L = layout()

for frame in range(FRAMES):
    nat_centers, node_centers, eks_y, eks_h = draw_base(cv, L)
    draw_traffic(cv, L, frame, FRAMES, nat_centers, node_centers, eks_y, eks_h)
    # Auto-advance page transition (0.12s per frame)
    cv.setPageTransition(duration=0.12, type='R')
    cv.showPage()

cv.save()
print(f"✅  architecture.pdf  ({FRAMES} frames — open in Acrobat/Preview and press ▶ or use full-screen mode)")
