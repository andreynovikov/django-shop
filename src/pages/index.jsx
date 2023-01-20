import Link from 'next/link';

import Layout from '@/components/layout';

export default function Index() {
    return (
        <div className="mt-4 text-center">
            <div className="d-inline-block">
                <Link href="/catalog/sewing_machines/">
                    <img src="/i/1.png" alt="Электромеханические швейные машины" width="290" height="290" />
                </Link>
                <Link href="/catalog/comp_sewing_machines/">
                    <img src="/i/2.png" alt="Компьютерные швейные машины" width="290" height="290" />
                </Link>
                <Link href="/catalog/sewing_embroidery_machines/">
                    <img src="/i/3.png" alt="Швейно-вышивальные машины" width="290" height="290" />
                </Link>
                <br/>
                <Link href="/catalog/overlock/">
                    <img src="/i/4.png" alt="Оверлоки, коверлоки и плоскошовные машины" width="290" height="290" />
                </Link>
                <Link href="/catalog/accessories/">
                    <img src="/i/5.png" alt="Аксессуары для машин Janome" width="290" height="290" />
                </Link>
            </div>
        </div>
    )
}

Index.getLayout = function getLayout(page) {
    return (
        <Layout hideTitle>
            {page}
        </Layout>
    )
}
